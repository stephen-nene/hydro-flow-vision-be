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

from typing import List, Dict, Any, Optional, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ToolResult(TypedDict):
    tool_name: str
    result: Dict[str, Any]
    error: Optional[str]


from langchain_google_genai import ChatGoogleGenerativeAI

from .tools import get_pump_details, AgentState

from .tools import analyse_lab_report,treatment_recommendation,ro_sizing,quotation_generator,proposal_generator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# Collect all tools
tools = [analyse_lab_report,treatment_recommendation,ro_sizing,quotation_generator,proposal_generator ]
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
class SequentialAgentState(TypedDict):
    """State for a sequential tool execution workflow."""
    messages: Annotated[Sequence[BaseMessage], add_messages] # Keep for logging/context if needed
    initial_request_data: Dict[str, Any] # Store the original formatted request
    tool_sequence: List[str]           # The sequence of tool names to execute
    current_tool_index: int            # Index of the next tool to run in the sequence
    tool_results: Dict[str, Any]       # Store results from successfully run tools
    error_log: List[str]               # Log errors encountered during execution
    final_output: Optional[Dict[str, Any]] # Store the final result after sequence completion


# Create a system message that explicitly instructs the model to use tools
# Mother AI System Message
from typing import Dict, List, Optional, TypedDict
from pydantic import BaseModel
import logging

# Define tool dependencies and data flow
TOOL_DEPENDENCY_MAP = {
    "analyse_lab_report": {
        "requires": ["customer_request", "guideline"],
        "provides": ["treatment_specs"],
        "description": "Analyzes water lab reports to generate treatment specifications"
    },
    "treatment_recommendation": {
        "requires": ["treatment_specs", "customer_request"],
        "provides": ["ro_system_specs"],
        "description": "Recommends treatment systems based on analysis"
    },
    "ro_sizing": {
        "requires": ["ro_system_specs", "customer_request"],
        "provides": ["sizing_details"],
        "description": "Calculates RO system sizing requirements"
    },
    "quotation_generator": {
        "requires": ["sizing_details", "customer_request"],
        "provides": ["cost_estimate"],
        "description": "Generates cost estimates for the system"
    },
    "proposal_generator": {
        "requires": ["ro_system_specs", "customer_request", "cost_estimate"],
        "provides": ["final_proposal"],
        "description": "Generates final customer proposal"
    }
}

class ToolExecutionResult(BaseModel):
    success: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    missing_inputs: Optional[List[str]] = None

def execute_tool_sequence(
    initial_data: Dict[str, Any],
    target_tool: Optional[str] = None,
    full_sequence: bool = False
) -> Dict[str, Any]:
    """
    Executes tools in logical sequence, automatically handling dependencies.
    
    Args:
        initial_data: Complete input data including customer_request and guideline
        target_tool: If specified, runs only up to this tool (with dependencies)
        full_sequence: If True, runs all tools regardless of target_tool
    
    Returns:
        Dictionary containing:
        - execution_sequence: List of tools executed
        - results: Outputs from each tool
        - final_output: Result from last executed tool
        - errors: Any encountered errors
    """
    context = initial_data.copy()
    execution_log = []
    errors = []
    
    # Determine execution sequence
    all_tools = list(TOOL_DEPENDENCY_MAP.keys())
    if target_tool:
        try:
            target_index = all_tools.index(target_tool)
            tool_sequence = all_tools[:target_index + 1]
        except ValueError:
            errors.append(f"Invalid target tool: {target_tool}")
            tool_sequence = all_tools if full_sequence else []
    else:
        tool_sequence = all_tools if full_sequence else []
    
    # Execute the determined sequence
    for tool_name in tool_sequence:
        tool = tools_by_name.get(tool_name)
        if not tool:
            errors.append(f"Tool not found: {tool_name}")
            continue
            
        # Check input requirements
        required_inputs = TOOL_DEPENDENCY_MAP[tool_name]["requires"]
        missing_inputs = [inp for inp in required_inputs if inp not in context]
        
        if missing_inputs:
            error_msg = f"Skipping {tool_name} - Missing inputs: {missing_inputs}"
            errors.append(error_msg)
            execution_log.append({
                "tool": tool_name,
                "status": "skipped",
                "reason": error_msg
            })
            continue
        
        try:
            # Prepare tool-specific input
            tool_input = {k: context[k] for k in required_inputs}
            
            # Execute tool
            result = tool.invoke(tool_input)
            
            # Validate output contains promised fields
            expected_outputs = TOOL_DEPENDENCY_MAP[tool_name]["provides"]
            if not all(out in result for out in expected_outputs):
                raise ValueError(f"Tool {tool_name} didn't provide expected outputs: {expected_outputs}")
            
            # Update context with results
            context.update(result)
            execution_log.append({
                "tool": tool_name,
                "status": "success",
                "inputs": tool_input,
                "outputs": result
            })
            
        except Exception as e:
            error_msg = f"Error in {tool_name}: {str(e)}"
            errors.append(error_msg)
            execution_log.append({
                "tool": tool_name,
                "status": "failed",
                "error": error_msg
            })
            if tool_name == target_tool:
                break  # Stop if target tool fails
    
    # Prepare final output
    final_output = None
    if execution_log and execution_log[-1]["status"] == "success":
        final_output = execution_log[-1]["outputs"]
    
    return {
        "execution_sequence": [entry["tool"] for entry in execution_log],
        "results": context,
        "final_output": final_output,
        "errors": errors,
        "success": len(errors) == 0
    }
# In mainai.py

def run_sequential_workflow(initial_data: Dict, tool_sequence: List[str]):
    """Runs the sequential workflow."""
    print(f"\n🚀 Starting Workflow with Sequence: {tool_sequence}\n")
    # print(f"Initial Data: {json.dumps(initial_data, indent=2)}\n")
    print("=" * 80)

    # Prepare the initial state for the SequentialAgentState
    initial_state = {
        "messages": [], # Initialize empty or with initial prompt if needed for logging
        "initial_request_data": initial_data,
        "tool_sequence": tool_sequence,
        # Other fields will be initialized by the 'start_workflow' node
        "current_tool_index": 0,
        "tool_results": {},
        "error_log": [],
        "final_output": None,
    }

    print("\n🤖 RUNNING WORKFLOW:\n")
    final_state = None
    try:
        # Stream values to see state changes
        for state_update in graph.stream(initial_state, stream_mode="values"):
            # Optional: Print state updates for debugging
            # print(f"--- State Update ---")
            # print(f"Current Index: {state_update.get('current_tool_index')}")
            # print(f"Results So Far: {state_update.get('tool_results', {}).keys()}")
            # print(f"Errors: {state_update.get('error_log')}")
            final_state = state_update

        print("\n" + "=" * 80)
        print("\n✅ WORKFLOW COMPLETE:\n")

        if final_state:
            print("Final Tool Results:")
            print(json.dumps(final_state.get('tool_results'), indent=2, ensure_ascii=False))
            if final_state.get('error_log'):
                print("\nErrors Encountered:")
                for error in final_state['error_log']:
                    print(f"- {error}")
            # print("\nFinal Output:")
            # print(json.dumps(final_state.get('final_output'), indent=2, ensure_ascii=False)) # If you have a final output step
        else:
            print("Workflow did not produce a final state.")

    except Exception as e:
        print(f"\n❌ WORKFLOW ERROR: {str(e)}")
        logger.error("Workflow execution failed", exc_info=True)

    print("\n" + "=" * 80)
    return final_state

# --- Example Usage ---
# Assuming 'formatted_customer_request' is the output from your formatting function
# formatted_request = format_customer_request_prompt(...) # Your existing function

# Define the sequence you want
# sequence_to_run = ["treatment_recommendation", "ro_sizing", "quotation_generator", "proposal_generator"]
# sequence_to_run = ["ro_sizing"] # Example: Run only one

# run_sequential_workflow(
#     initial_data=formatted_request, # Pass the structured initial data
#     tool_sequence=sequence_to_run
# )

