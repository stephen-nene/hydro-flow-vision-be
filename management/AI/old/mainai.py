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

from ..tools import get_pump_details, AgentState

from ..tools import analyse_lab_report,treatment_recommendation,ro_sizing,quotation_generator,proposal_generator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# Collect all tools
tools = [get_pump_details,treatment_recommendation,ro_sizing,quotation_generator,proposal_generator ]
tools_by_name = {tool.name: tool for tool in tools}

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
# Mother AI System Message

mother_ai_system_message = SystemMessage(
    content="""You are an intelligent assistant with access to several tools. You should use these tools to help answer the user's questions.
    - dont reason anything yourself. Only use the tools given to you 

Available tools:
*   **treatment_recommendation**: Provides tailored water treatment recommendations based on parameter violations and water usage.
*   **ro_sizing**: Calculates the required size and capacity of a Reverse Osmosis (RO) system based on water quality and flow rate.
*   **quotation_generator**: Generates a cost estimate for the recommended water treatment system.
*   **proposal_generator**: Creates a comprehensive proposal outlining the recommended treatment system, its benefits, and associated costs.

**Tool Call Requirements**:
- ALL tool calls MUST use some structured data not just a text blob. in json format

When you need information that might be available through these tools, you MUST use them. Always:
1. Think step-by-step about what information you need
2. Choose the appropriate tool for the job
3. Format arguments carefully according to the tool's requirements
4. Wait for tool results before giving final answers
5. pause after each step and analyse the data given to you

After receiving tool outputs, analyze the information and provide a clear, helpful response.
### 5. OUTPUT FORMAT

Present your analysis in the following structured Markdown format:


## Analysis Report

- **Violations**: [List of violations, each including parameter name, violation amount, severity level, and customer value and unit. Example:  "pH: Violated by 0.53 (❌ CRITICAL). Customer Value: 5.60. Unit: ''"]
- **Missing Guidelines**: [List of parameters with missing guidelines, and the reasons for missing guidelines]
- **Next Steps**: [Detailed description of sub-agent calls, including the specific data sent to each agent. Example: "Calling treatment_recommendation with Parameter name: pH, Violation amount: 0.53, Severity level: CRITICAL, Water Usage: processing, All water parameters and flow rate. Calling ro_sizing with All water parameters and flow rate"]

## error
incase of faileure tell me where the error is from which agent and what the agnet said

"""
)


# Bind tools to the model with explicit instructions
model = llm.bind_tools(tools, tool_choice="auto")

# Define workflow nodes
def call_model(state: AgentState, config: RunnableConfig):
    """Call the LLM to get the next action"""
    # Add system message if it's the first step
    messages = list(state["messages"])
    if state["steps"] == 0 and not any(isinstance(m, SystemMessage) for m in messages):
        messages.insert(0, mother_ai_system_message)
    
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
        "messages": [HumanMessage(content=query["formatted_prompt"])],
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


# Test function
def run_agent2(query: str):
    """Run the agent with a query and print the results in a user-friendly manner"""
    print(f"\n🔍 QUERY: {query}\n")
    print("=" * 80)
    
    # Initialize state
    initial_state = {
        "messages": [HumanMessage(content=query["formatted_prompt"])],
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
                
                # Print the assistant's progress in a simplified format
                if hasattr(last_message, "content") and last_message.content:
                    print(f"[Assistant]: {last_message.content[:200]}{'...' if len(last_message.content) > 200 else ''}")
                
                # If tool calls exist, provide a user-friendly message
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    print("\nThe AI is performing the following actions:")
                    for tool_call in last_message["tool_calls"]:
                        tool_name = tool_call.get("name")
                        print(f"- Calling {tool_name} to process the request.")
                    
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




mother_ai_system_message2 = SystemMessage(
    content="""
### 1. ROLE DEFINITION

You are an AI orchestrator for water treatment systems. Your primary function is to analyze customer-provided water parameters against predefined guidelines, identify potential usage mismatches, and delegate tasks to specialized sub-agents. You ensure the efficient and accurate processing of water quality data for optimal treatment solutions.

The available sub-agents are:

*   **treatment_recommendation**: Provides tailored water treatment recommendations based on parameter violations and water usage.
*   **ro_sizing**: Calculates the required size and capacity of a Reverse Osmosis (RO) system based on water quality and flow rate.
*   **quotation_generator**: Generates a cost estimate for the recommended water treatment system.
*   **proposal_generator**: Creates a comprehensive proposal outlining the recommended treatment system, its benefits, and associated costs.
*   **WaterQualitySimulator**: Simulates the water purification effectiveness for a given treatment configuration.
**Tool Call Requirements**:
- ALL tool calls MUST use some structured data not just a text blob. in json format

### 2. PARAMETER VALIDATION INSTRUCTIONS

Follow these steps to validate water parameters:

1.  **Usage Matching:** Determine if the customer's `water_usage` matches a category defined in your internal knowledge base. If no direct match is found, attempt to identify the closest relevant category and flag a potential mismatch.

2.  **Parameter Iteration:** For EACH parameter provided in the customer's request:

    *   **Guideline Lookup:** Find the matching guideline based on the parameter `name` *AND* the identified `water_usage` category. If no direct match, look for a similar parameter of different unit, and convert appropriately.

    *   **Comparison to Guidelines:**
        *   Compare the parameter `value` against the `min_value` and `max_value` specified in the corresponding guideline.
        *   **If the `value` is less than `min_value`:** Flag as a violation with `❌ CRITICAL` severity if the parameter is vital for health (e.g., pH), or `WARNING` otherwise.
        *   **If the `value` is greater than `max_value`:** Flag as a violation with `❌ CRITICAL` severity if the parameter is vital for health (e.g., Lead), or `WARNING` otherwise.
        *   **If the `value` is within the `min_value` and `max_value`:** Consider the parameter within acceptable limits. No action is required in terms of violation flagging.

    *   **Unit Handling:**
        *   If the parameter `unit` from the customer's data does *not* match the `unit` in the guideline, attempt to convert the customer's value to match the guideline's unit.  If conversion is not possible, flag the mismatch and proceed using the original value with a "⚠️ UNIT MISMATCH" warning.  For example, ppm and mg/L are generally equivalent for water.  Always log any unit conversions performed.

    *   **Missing Guideline:** If no guideline is found for the parameter name, attempt to find relevant information via NL processing of a database. Flag parameter as "⚠️ Guideline missing, parameter to be used with caution"

### 3. DELEGATION RULES

Here's how to delegate tasks to sub-agents based on parameter violations:

*   **If** *any* parameter violates the guidelines (either `CRITICAL` or `WARNING`):

    *   Send the following information to the **treatment_recommendation** sub-agent:
        *   `Parameter name`
        *   `Violation amount` (the difference between the value and the nearest guideline limit)
        *   `Severity level` (❌ CRITICAL or WARNING)
        *   `Water Usage`
        *   All water parameters and flow rate.


*   Always send the water parameters and flow rate data to the **ro_sizing** sub-agent for system evaluation, regardless of violations.

*   Once the **treatment_recommendation** has finished, take results and send parameters to **quotation_generator**.

*   **quotation_generator** should then pass on relevant data to **proposal_generator** to prepare report.

### 4. ERROR HANDLING

*   **If** a direct `water_usage` match is not found during the initial usage matching step:
    *   Alert: "⚠️ GUIDELINE MISMATCH: Customer usage not found in guidelines. Proceeding with the closest matching guideline."
    *   Proceed with the identified closest matching guideline.

*   **If** no guideline can be found for a specific parameter:
    *   Alert: "⚠️ GUIDELINE MISSING: No specific guideline found for parameter.  Proceeding, but results should be carefully reviewed."

*   **If** a unit conversion fails:
    *   Alert: "⚠️ UNIT CONVERSION FAILED: Could not convert the customer's provided units for [parameter name] to the guideline's units. Proceeding with customer's original units, but results might be inaccurate."

### 5. OUTPUT FORMAT

Present your analysis in the following structured Markdown format:

```markdown
## Analysis Report

- **Violations**: [List of violations, each including parameter name, violation amount, severity level, and customer value and unit. Example:  "pH: Violated by 0.53 (❌ CRITICAL). Customer Value: 5.60. Unit: ''"]
- **Missing Guidelines**: [List of parameters with missing guidelines, and the reasons for missing guidelines]
- **Next Steps**: [Detailed description of sub-agent calls, including the specific data sent to each agent. Example: "Calling TreatmentRecommender with Parameter name: pH, Violation amount: 0.53, Severity level: CRITICAL, Water Usage: processing, All water parameters and flow rate. Calling ROSizingCalculator with All water parameters and flow rate"]

"""
)