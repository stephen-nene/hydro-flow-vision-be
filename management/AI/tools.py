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


# Initialize the LLM
llm = ChatOpenAI(
    # model="deepseek-ai/deepseek-r1",
    model='meta/llama-4-scout-17b-16e-instruct',
    # model="google/gemma-3-27b-it",
    temperature=0.3,  
    max_tokens=1024,
    timeout=30,
#   top_p=0.7,
    max_retries=3,
    api_key=config('NVIDIA_SECRET_KEY'),
    base_url="https://integrate.api.nvidia.com/v1",

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