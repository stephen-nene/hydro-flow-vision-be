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

class FormatCustomerRequestInput(BaseModel):
    customer_location: str
    water_source: str
    water_usage: str
    daily_flow_rate: float
    daily_water_requirement: float
    # budget_amount: float
    # budget_currency: str
    water_parameters: list
    notes: str = "No extra notes provided."
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

@tool("formart customer request", args_schema=FormatCustomerRequestInput)
def format_customer_request_prompt(    
    customer_location: str,
    water_source: str,
    water_usage: str,
    daily_flow_rate: float,
    daily_water_requirement: float,
    # budget_amount: float,
    # budget_currency: str,
    water_parameters: List[Dict[str, Any]],
    notes: str = "No extra notes provided."
) -> Dict[str, Any]:
    """
    Take a customer request and format it into a nice format that the AI can understand.
    """
    water_details = "\n".join([
        f"- {p['name']}: {p['value']} {p['unit']}" for p in water_parameters
    ])

    # Raw and formatted prompts for the AI
        # Budget: {budget_amount} {budget_currency}
        # Daily Flow Rate: {daily_flow_rate} L/day
    raw_prompt = f"""
        You are preparing a technical brief for a customer water treatment request.

    This summary will be used as the first step in an automated process where other AI models and tools will handle specific tasks such as RO sizing, treatment recommendations, and cost estimation.

    Your role is to:
    - **Analyze the provided lab report** and create a human-readable project initiation summary.
    - **Do not recommend treatments** or suggest RO sizing, as these will be handled by other specialized tools later in the process.
    - **Focus on presenting key aspects** relevant to system sizing, pretreatment, and costing in a clear, accessible way for downstream tools.

    I have other tools that will handle further processing, t i.e:
    - **Treatment Recommendation**: Will provide detailed recommendations based on the lab analysis.
    - **RO Sizing**: Will calculate the required size of the reverse osmosis system.
    - **Quotation Generator**: Will generate a quotation based on the treatment and RO sizing data.
    - **Proposal Generator**: Will generate a final proposal based on the overall system design.

    Begin by generating a summary in markdown format that presents the water quality parameters and any key observations relevant for system sizing and pretreatment. Highlight any unusual values and make sure the summary is clear and technical, but easy to understand.
        Use the following details to create a professional project initiation summary that will be used in an automated design and proposal generation process for a reverse osmosis (RO) system.


        Location: {customer_location}
        Water Source: {water_source}
        Usage: {water_usage}
        Daily Requirement: {daily_water_requirement} L/day
        Notes: {notes}

        Water lab parameters:
        {water_details}

        **Important Notes:**
        - Do not recommend RO sizing or specific treatment options (e.g., filtration, dechlorination, etc.) as these will be handled by other specialized AI models and agents.
        - Do not generate a quotation or proposal. These will be generated by the **quotation_generator** and **proposal_generator** tools.
        - Focus on creating a clean, human-readable **project initiation summary** in **markdown format** to kickstart the design and proposal process.
        - Include context on system sizing, pretreatment considerations, and potential costing factors without making specific recommendations.

        Your task is to provide a clear and concise summary that will be used by the subsequent tools to continue the process. Highlight any values in the water analysis that are unusual or require attention, and maintain a professional, easy-to-understand tone.
    """.strip()

    #     **Notes**: Please ensure that all values are checked against the acceptable guidelines and highlight any discrepancies.

    # Make sure to highlight any values that are outside the acceptable range, as these will be important for the downstream tools to address. The goal is to prepare the data in a clean, readable format for the subsequent processing steps.

    # raw_prompt = f"""
    #     You are preparing a technical brief for a customer water treatment request. 
    #     Use the following details to create a professional project initiation summary that will be used in an automated design and proposal generation process for a reverse osmosis (RO) system.

    #     **Location**: {customer_location}
    #     **Water Source**: {water_source}
    #     **Usage**: {water_usage}
    #     **Daily Requirement**: {daily_water_requirement} L/day
    #     **Notes**: {notes}

    #     **Water Lab Parameters**: 
    #     {water_details}

    #     Your role:
    #     - Analyze the provided water quality parameters to create a clean, actionable summary in markdown format.
    #     - Highlight any unusual values or parameters that may require special attention during design (like turbidity, iron, chlorine, etc.).
    #     - **Do not** provide treatment recommendations, RO sizing, or pricing as these will be handled by other AI models and tools.
    #     - Focus on generating a professional, human-readable summary of the request that can be used by other tools downstream (like RO Sizing, Treatment Recommendations, etc.).
    #     - Ensure that the summary is clear and technical but accessible, pointing out any anomalies and considerations for system sizing, pretreatment, and costing.

    #     The following parameters are provided for you to review and analyze:
    #     {{"Lead": "{lead_min} to {lead_max} mg/L",
    #     "Alkalinity": "{alkalinity_min} to {alkalinity_max} mg/L",
    #     "pH": "{ph_min} to {ph_max}",
    #     "Sodium": "{sodium_min} to {sodium_max} mg/L",
    #     "Hardness": "{hardness_min} to {hardness_max} mg/L",
    #     "TDS": "{tds_min} to {tds_max} mg/L",
    #     "Fluoride": "{fluoride_min} to {fluoride_max} mg/L",
    #     "Chlorine": "{chlorine_min} to {chlorine_max} mg/L",
    #     "Iron": "{iron_min} to {iron_max} mg/L",
    #     "Nitrate": "{nitrate_min} to {nitrate_max} mg/L",
    #     "Electrical Conductivity": "{conductivity_min} to {conductivity_max} μS/cm"}}
        
    #     **Key Areas to Address**:
    #     - Pretreatment needs: Filter out any unusual values (e.g., high turbidity, chlorine, iron) and highlight potential pretreatment steps.
    #     - Water Quality Issues: Point out any parameters that fall outside the recommended ranges (e.g., lead, fluoride, nitrate).
    #     - System Sizing: The system should be sized to meet the daily water demand based on the provided water source capacity.

    #     Make sure the information is ready for further processing by subsequent tools (such as RO Sizing, Treatment Recommendation, Quotation Generator, and Proposal Generator).
    # """.strip()

    #         Generate a natural-sounding, human-readable summary of this request in **markdown format**.
    # Focus on system sizing, pretreatment, and costing. Highlight any unusual values and keep the tone clean, technical, and easy to understand.
    # Use appropriate markdown elements such as headings, bullet points, and paragraphs.

        # Their budget is {budget_amount} {budget_currency}.
    prompt = f"""
        We received a water treatment request from a client located in {customer_location}.
        They are using {water_source} water for {water_usage}, and require approximately {daily_water_requirement} L/day at a flow rate of {daily_flow_rate} L/hr.

        The client provided a water analysis report with the following parameters:
        {water_details}

        Notes from the client: "{notes}"

        Begin by analyzing this lab report for treatment recommendations.
        Consider pretreatment, RO sizing, chemical dosing, and prepare to generate a complete water treatment proposal.
    """.strip()

    result = llm.invoke(raw_prompt)

    return {
        "formatted_prompt": result.content
    }




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