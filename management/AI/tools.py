import os
from dotenv import load_dotenv
from typing import Annotated, Sequence, TypedDict, Dict, Any, List, Optional,Union
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
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
# Initialize the LLM
llm2 = ChatOpenAI(
    model="deepseek-ai/deepseek-r1",
    # model='meta/llama-4-scout-17b-16e-instruct',
    # model="google/gemma-3-27b-it",
    temperature=0.3,  
    max_tokens=1024,
    timeout=30,
#   top_p=0.7,
    max_retries=3,
    api_key=config('NVIDIA_SECRET_KEY'),
    base_url="https://integrate.api.nvidia.com/v1",

)

# Create LLM class
llm = ChatGoogleGenerativeAI(
    model= "gemini-2.0-flash",
    temperature=1.0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    google_api_key=config('GOOGLE_SECRET_KEY'),
)


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# Define the agent state
class AgentState(TypedDict):
    """The state of the agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    steps: int

# Define input schemas for tools
class PumpSearchInput(BaseModel):
    model_name: str = Field(description="The model name of the pump to search for")

class WaterParameter(BaseModel):
    name: str
    value: Optional[float]
    unit: Optional[str]


class GuidelineParameter(BaseModel):
    name: str
    unit: Optional[str]
    min_value: Optional[float]
    max_value: Optional[float]


class CustomerRequestInput(BaseModel):
    location: str
    water_source: str
    water_usage: str
    daily_flow_rate: int
    budget: Dict[str, Union[int, float, str]]
    water_parameters: List[WaterParameter]
    notes: Optional[str] = "No additional notes provided."


class FormatCustomerRequestInput(BaseModel):
    customer_request: CustomerRequestInput
    guideline: Optional[List[GuidelineParameter]]
    ai_settings: Optional[Dict[str, Union[str, float, int, bool]]] = {}


class AnalyseLabReportInput(BaseModel):
    # it will be a documnet/cvc of the lab results
    text: str = Field(description="Text to analyze")

class TreatmentRecommendationInput(BaseModel):
    # it will be a documnet/cvc of the lab results
    text: str = Field(description="Text to analyze")

class ROSizingInput(BaseModel):
    # it will be a documnet/cvc of the lab results
    text: str = Field(description="Text to analyze")

class QuotationGeneratorInput(BaseModel):
    # it will be a documnet/cvc of the lab results
    text: str = Field(description="Text to analyze")

class ProposalGeneratorInput(BaseModel):
    # it will be a documnet/cvc of the lab results
    text: str = Field(description="Text to analyze")

# @tool("formart customer request", args_schema=FormatCustomerRequestInput)
@tool("format customer request")
def format_customer_request_prompt(
    customer_request: Dict,  # Water treatment parameters and requirements
    guideline: Optional[List[Dict]] = None,  # Water quality guidelines/standards
    ai_settings: Optional[Dict] = None  # LLM configuration parameters
) -> Dict:
    """
    Generates a prompt for the Mother Agent that will coordinate water treatment solutions.
    This function doesn't provide recommendations itself but prepares data for delegation.
    """
    try:


        # Process parameters and prepare data for the Mother Agent
        location = customer_request.get('location', 'Unknown')
        water_source = customer_request.get('water_source', 'Unknown')
        water_usage = customer_request.get('water_usage', 'Unknown')
        daily_flow_rate = customer_request.get('daily_flow_rate', 0)
        budget = customer_request.get('budget', {})
        budget_amount = budget.get('amount', 0)
        budget_currency = budget.get('currency', 'KES')
        notes = customer_request.get('notes', '')
        
        # Analyze water parameters against guidelines
        water_params_status = []
        if guideline and 'water_parameters' in customer_request:
            for param in customer_request['water_parameters']:
                param_name = param.get('name')
                param_value = param.get('value')
                param_unit = param.get('unit', '')
                
                # Find matching guideline
                matching_guide = next((g for g in guideline if g.get('name') == param_name), None)
                
                if matching_guide:
                    min_value = matching_guide.get('min_value')
                    max_value = matching_guide.get('max_value')
                    
                    # Determine status
                    status = "WITHIN RANGE"
                    if param_value < min_value:
                        status = "BELOW STANDARD"
                    elif param_value > max_value:
                        status = "ABOVE STANDARD"
                    
                    water_params_status.append({
                        "name": param_name,
                        "value": param_value,
                        "unit": param_unit,
                        "min_value": min_value,
                        "max_value": max_value,
                        "status": status
                    })
                else:
                    water_params_status.append({
                        "name": param_name,
                        "value": param_value,
                        "unit": param_unit,
                        "status": "NO GUIDELINE"
                    })

        # Create the raw prompt for the Mother Agent
        raw_prompt = f"""
        # MOTHER AGENT INSTRUCTION: WATER TREATMENT SYSTEM COORDINATION
        
        You are the Mother Agent responsible for coordinating a complete water treatment solution. Your task is to analyze the provided customer data and delegate specialized tasks to your team of expert agents. DO NOT attempt to provide treatment recommendations yourself - your role is coordination and delegation.
        
        ## CUSTOMER REQUEST DATA
        - Location: {location}
        - Water Source: {water_source}
        - Water Usage Purpose: {water_usage}
        - Daily Flow Rate: {daily_flow_rate} liters per day
        - Budget: {budget_amount} {budget_currency}
        - Additional Notes: {notes}
        
        ## WATER QUALITY PARAMETERS ANALYSIS
        """
        
        # Add water parameters with status
        for param in water_params_status:
            if "min_value" in param:
                raw_prompt += f"\n- {param['name']}: {param['value']} {param['unit']} (Standard: {param['min_value']} - {param['max_value']} {param['unit']}) - **{param['status']}**"
            else:
                raw_prompt += f"\n- {param['name']}: {param['value']} {param['unit']} - **{param['status']}**"
        
        raw_prompt += f"""
        
        ## AVAILABLE SPECIALIZED AGENTS
        You have access to the following specialized agents that you must coordinate with:
        
        1. **Treatment Recommendation Agent**: Analyze water parameters and recommend appropriate treatment methods
           - Input: Water parameters, usage requirements, location factors
           - Output: Detailed treatment process recommendations
        
        2. **RO Sizing Agent**: Calculate reverse osmosis system specifications
           - Input: Water parameters, daily flow rate, treatment requirements
           - Output: RO system sizing and specifications
        
        3. **Quotation Generator Agent**: Produce accurate cost estimates
           - Input: Treatment recommendations, RO sizing, customer budget constraints
           - Output: Detailed quotation with item-by-item breakdown
        
        4. **Proposal Generator Agent**: Create customer-ready proposals
           - Input: All previous agent outputs, customer requirements
           - Output: Comprehensive treatment proposal document
        
        ## YOUR COORDINATION TASKS:
        1. Review the water parameter analysis above and identify which parameters require treatment attention
        2. Determine which specialized agents need to be activated based on the customer requirements
        3. Prepare specific instructions for each agent you plan to activate
        4. Create a workflow sequence for the agents, ensuring each has the inputs it needs
        5. Do NOT attempt to provide technical recommendations or solutions yourself
        
        Proceed with your coordination role by analyzing the data and preparing instructions for your specialized agents.
        """
        
        result = llm.invoke(raw_prompt)
        
        return {
            "formatted_data": {
                "customer_request": customer_request,
                "guidelines": guideline,
                "parameters_analysis": water_params_status
            },
            "formatted_prompt": result.content
        }
        
    except Exception as e:
        logger.error(f"Error in format_customer_request_prompt: {e}")
        raise


        # Raw and formatted prompts for the AI
            # Budget: {budget_amount} {budget_currency}
            # Daily Flow Rate: {daily_flow_rate} L/day
        # raw_prompt = f"""
        #         You are preparing a technical brief for a customer water treatment request.

        #     This summary will be used as the first step in an automated process where other AI models and tools will handle specific tasks such as RO sizing, treatment recommendations, and cost estimation.

        #     Your role is to:
        #     - **Analyze the provided lab report** and create a human-readable project initiation summary/prompt that will be used to initiate an agentic system for water purification.
        #     - **Do not recommend treatments** or suggest RO sizing, as these will be handled by other specialized tools later in the process.
        #     - **Focus on presenting key aspects** relevant to system sizing, pretreatment, and costing in a clear, accessible way for downstream tools.

        #     I have other tools (AI agents) that will handle further processing, i.e:
        #     - **Treatment Recommendation**: Will provide detailed recommendations based on the lab analysis.
        #     - **RO Sizing**: Will calculate the required size of the reverse osmosis system.
        #     - **Quotation Generator**: Will generate a quotation based on the treatment and RO sizing data.
        #     - **Proposal Generator**: Will generate a final proposal based on the overall system design.

        #     Begin by generating a summary in markdown format that presents the water quality parameters and any key observations relevant for system sizing and pretreatment. Highlight any unusual values and make sure the summary is clear and technical, but easy to understand.
        #         Use the following details to create a professional project initiation summary that will be used in an automated design and proposal generation process for a reverse osmosis (RO) system.


        #         Location: {customer_location}
        #         Water Source: {water_source}
        #         Usage: {water_usage}        - Include context on system sizing, pretreatment considerations, and potential costing factors without making specific recommendations.

        #         Daily Requirement: {daily_water_requirement} L/day
        #         Notes: {notes}

        #         Water lab parameters:
        #         {water_details}

        #         **Important Notes:**
        #         - Do not recommend RO sizing or specific treatment options (e.g., filtration, dechlorination, etc.) as these will be handled by other specialized AI models and agents.
        #         - Do not generate a quotation or proposal. These will be generated by the **quotation_generator** and **proposal_generator** tools.
        #         - Focus on creating a clean, human-readable **project initiation summary** in **markdown format** to kickstart the fully automated agents.

        #         Your task is to provide a clear and concise summary that will be used to iniatite an agentic system. Highlight any values in the water analysis that are unusual or require attention, and maintain a professional, easy-to-understand tone.
        #     """.strip()
        
        # prompt = f"""
        #     We received a water treatment request from a client located in {customer_location}.
        #     They are using {water_source} water for {water_usage}, and require approximatelywater at a flow rate of {daily_flow_rate} L/hr.

        #     The client provided a water analysis report with the following parameters:
        #     {water_details}

        #     Notes from the client: "{notes}"

        #     Begin by analyzing this lab report for treatment recommendations.
        #     Consider pretreatment, RO sizing, chemical dosing, and ptreatmentrepare to generate a complete water  proposal.
        # """.strip()







@tool("analyse_lab_report", args_schema=AnalyseLabReportInput)
def analyse_lab_report(report: str) -> Dict[str, Any]:
    """
    Take a lab report and analyze it to parse the data into a nice formart that the AI can analyse
    """
    # ocr

@tool("treatment_recommendation", args_schema=TreatmentRecommendationInput)
def treatment_recommendation(report: str) -> Dict[str, Any]:
    """
    Take a analysed lab report and provides a treatment recommendations
    """


@tool("RO Sizing", args_schema=ROSizingInput)
def ro_sizing(report: str) -> Dict[str, Any]:
    """
    With the analysed lab report, provides the RO sizing from the companies database
    """

@tool("quotation_generator",args_schema=QuotationGeneratorInput)
def quotation_generator(report: str) -> Dict[str, Any]:
    """
    With the analysed lab report and the RO sizing, gives the quotation for the customer
    """

@tool("proposal_generator",args_schema=ProposalGeneratorInput)
def proposal_generator(report: str) -> Dict[str, Any]:
    """
    With the analysed lab report and the RO sizing, gives the proposal for the customer
    """




# Define tools
@tool("get_pump_details", args_schema=PumpSearchInput)
def get_pump_details(model_name: str) -> Dict[str, Any]:
    """
    Retrieves pump details for a given pump model from the database.
    """
    try:
        # Simulate ERP lookup with mock data for testing
        pump_database = {
            "ddp60": {
                "Model Number": "DDP60",
                "Product_Model": "DDP 60",
                "Description": "Davis & Shirtliff domestic water pump from stevonene pumps",
                "Inventory": 15,
                "Retail_Price": 12500,
                "Max_Flow_Rate": 3000,  # L/h
                "Max_Head": 40,  # meters
                "Power": 0.37  # kW
            },
            "ddp100": {
                "Model Number": "DDP100",
                "Product_Model": "DDP 100",
                "Description": "Davis & Shirtliff high pressure water pump",
                "Inventory": 8,
                "Retail_Price": 18500,
                "Max_Flow_Rate": 6000,  # L/h
                "Max_Head": 55,  # meters
                "Power": 0.75  # kW
            },
            "danfoss": {
                "Model Number": "DANFOSS-IEC180",
                "Product_Model": "DANFOSS IEC 180 22KW 3PH 4 POLE MOTOR",
                "Description": "Industrial motor pump for high demand applications",
                "Inventory": 3,
                "Retail_Price": 125000,
                "Max_Flow_Rate": 12000,  # L/h
                "Max_Head": 80,  # meters
                "Power": 22  # kW
            }
        }
        
        # Search for the pump (case insensitive)
        model_key = model_name.lower().replace(" ", "").replace("-", "")
        
        # Direct match
        if model_key in pump_database:
            return pump_database[model_key]
        
        # Partial match
        for key, data in pump_database.items():
            if (model_key in key or 
                model_key in data["Product_Model"].lower().replace(" ", "") or
                model_key in data["Description"].lower()):
                return data
                
        return {"error": f"No pump found with model name matching '{model_name}'. Please check the model name and try again."}
    except Exception as e:
        logger.error(f"Error in get_pump_details: {e}")
        return {"error": str(e)}