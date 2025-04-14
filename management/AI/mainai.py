import os
from dotenv import load_dotenv
from typing import Annotated, Sequence, TypedDict, Dict, Any, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import requests
from requests.auth import HTTPBasicAuth
from langchain_openai import ChatOpenAI
from decouple import config
import json
import logging
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from langchain_google_genai import ChatGoogleGenerativeAI

from tools import get_pump_details, get_weather, calculator, unit_converter, AgentState

from tools import analyse_lab_report,treatment_recommendation,ro_sizing,quotation_generator,proposal_generator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# Collect all tools
tools = [get_pump_details, get_weather, calculator, unit_converter]
tools_by_name = {tool.name: tool for tool in tools}

# Initialize the LLM
# llm = ChatOpenAI(
#     # model="deepseek-ai/deepseek-r1",
#     model='meta/llama-4-scout-17b-16e-instruct',
#     # model="google/gemma-3-27b-it",
#     temperature=0.3,  
#     max_tokens=1024,
#     timeout=30,
# #   top_p=0.7,
#     max_retries=3,
#     api_key=config('NVIDIA_SECRET_KEY'),
#     base_url="https://integrate.api.nvidia.com/v1",

# )

# Create LLM class
llm = ChatGoogleGenerativeAI(
    model= "gemini-2.0-flash",
    temperature=1.0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    google_api_key=config('GOOGLE_SECRET_KEY'),
)

# Create a system message that explicitly instructs the model to use tools
system_message = SystemMessage(
    content="""You are an intelligent assistant with access to several tools. You should use these tools to help answer the user's questions.

Available tools:
1. get_pump_details - Use this to look up information about specific pump models in the database
2. get_weather - Use this to check weather conditions in different locations
3. calculator - Use this to perform mathematical calculations
4. unit_converter - Use this to convert between different units of measurement

When you need information that might be available through these tools, you MUST use them. Always:
1. Think step-by-step about what information you need
2. Choose the appropriate tool for the job
3. Format arguments carefully according to the tool's requirements
4. Wait for tool results before giving final answers
5. pause after each step and analyse the data given to you

After receiving tool outputs, analyze the information and provide a clear, helpful response.
"""
)

# Bind tools to the model with explicit instructions
model = llm.bind_tools(tools)

# Define workflow nodes
def call_model(state: AgentState, config: RunnableConfig):
    """Call the LLM to get the next action"""
    # Add system message if it's the first step
    messages = list(state["messages"])
    if state["steps"] == 0 and not any(isinstance(m, SystemMessage) for m in messages):
        messages.insert(0, system_message)
    
    # Call the model
    try:
        logger.info("Calling model with messages")
        response = model.invoke(messages, config)
        logger.info(f"Model response received: {response}")
        
        # Track if tool calls were made
        if hasattr(response, "tool_calls") and response.tool_calls:
            logger.info(f"Tool calls detected: {response.tool_calls}")
        else:
            logger.info("No tool calls detected in response")
        
        return {"messages": [response], "steps": state["steps"] + 1}
    except Exception as e:
        logger.error(f"Error calling model: {e}")
        error_message = SystemMessage(content=f"Error calling model: {str(e)}")
        return {"messages": [error_message], "steps": state["steps"] + 1}

def call_tools(state: AgentState):
    """Process any tool calls from the LLM"""
    outputs = []
    last_message = state["messages"][-1]
    
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        logger.info("No tool calls found in message")
        return {"messages": [], "steps": state["steps"]}
    
    logger.info(f"Processing {len(last_message.tool_calls)} tool calls")
    
    for tool_call in last_message.tool_calls:
        try:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
            
            if tool_name in tools_by_name:
                tool_result = tools_by_name[tool_name].invoke(tool_args)
                logger.info(f"Tool result: {tool_result}")
                
                outputs.append(
                    ToolMessage(
                        content=json.dumps(tool_result, ensure_ascii=False),
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
            else:
                error_msg = f"Tool '{tool_name}' not found"
                logger.error(error_msg)
                outputs.append(
                    ToolMessage(
                        content=json.dumps({"error": error_msg}, ensure_ascii=False),
                        name="error",
                        tool_call_id=tool_call["id"],
                    )
                )
        except Exception as e:
            logger.error(f"Error processing tool call: {e}")
            outputs.append(
                ToolMessage(
                    content=json.dumps({"error": str(e)}, ensure_ascii=False),
                    name="error",
                    tool_call_id=tool_call["id"] if "id" in tool_call else "unknown",
                )
            )
    
    return {"messages": outputs, "steps": state["steps"]}

def should_continue(state: AgentState):
    """Determine whether to continue the conversation or end it"""
    # Check if we've hit step limit
    if state["steps"] >= 10:
        logger.info("Reached maximum steps (10), ending conversation")
        return "end"
        
    # Check if the last message has tool calls
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info("Tool calls detected, continuing to tools node")
        return "continue_to_tools"
        
    # Check if the last message is from a tool
    if isinstance(last_message, ToolMessage):
        logger.info("Tool message detected, continuing to agent")
        return "continue_to_agent"
        
    # Otherwise end the conversation
    logger.info("No further actions needed, ending conversation")
    return "end"

# Build the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tools)

# Set entry point
workflow.set_entry_point("agent")

# Add edges
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue_to_tools": "tools",
        "continue_to_agent": "agent",
        "end": END,
    },
)

workflow.add_conditional_edges(
    "tools",
    should_continue,
    {
        "continue_to_tools": "tools",
        "continue_to_agent": "agent",
        "end": END,
    },
)

# Compile the graph
graph = workflow.compile()

# Test function
def run_agent(query: str):
    """Run the agent with a query and print the results"""
    print(f"\n🔍 QUERY: {query}\n")
    print("=" * 80)
    
    # Initialize state
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "steps": 0
    }
    
    # Run the graph
    print("\n🤖 RUNNING AGENT:\n")
    final_state = None
    
    try:
        for i, state in enumerate(graph.stream(initial_state, stream_mode="values")):
            print(f"\n--- Step {i+1} ---")
            if state["messages"]:
                last_message = state["messages"][-1]
                
                if hasattr(last_message, "content") and last_message.content:
                    print(f"[{last_message.type}]: {last_message.content[:200]}{'...' if len(last_message.content) > 200 else ''}")
                
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    print(f"Tool Calls: {json.dumps(last_message.tool_calls, indent=2)}")
            
            final_state = state
        
        print("\n" + "=" * 80)
        print("\n✅ FINAL RESPONSE:\n")
        
        # Find the last assistant message
        assistant_messages = [msg for msg in final_state["messages"] if msg.type == "ai"]
        if assistant_messages:
            print(assistant_messages[-1].content)
        else:
            print("No final response from assistant.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        
    print("\n" + "=" * 80)
    return final_state

# Example usage
if __name__ == "__main__":
    # Test queries
    queries = [
        "Can you get me details about the DDP 69 pump?",
        # "What's the weather like in Nairobi today?",
        # "Calculate 125 * 8.5 - 42",
        # "Convert 30 meters to feet",
        # "Would the DANFOSS IEC 180 pump be suitable for a job requiring 1000 L/h flow rate and a 30m head?"
    ]
    
    for query in queries:
        run_agent(query)