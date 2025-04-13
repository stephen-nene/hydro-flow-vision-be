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

class WeatherInput(BaseModel):
    location: str = Field(description="City or location to get weather for")

class CalculatorInput(BaseModel):
    expression: str = Field(description="Mathematical expression to evaluate")

class ConversionInput(BaseModel):
    value: float = Field(description="Value to convert")
    from_unit: str = Field(description="Source unit (e.g., 'meters', 'feet', 'liters')")
    to_unit: str = Field(description="Target unit (e.g., 'meters', 'feet', 'liters')")

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

@tool("get_weather", args_schema=WeatherInput)
def get_weather(location: str) -> Dict[str, Any]:
    """
    Retrieves current weather data for a given location.
    """
    try:
        # Simulate weather API call with mock data
        weather_data = {
            "nairobi": {
                "temperature": 22,
                "condition": "Partly Cloudy",
                "humidity": 65,
                "wind_speed": 12,
                "location": "Nairobi, Kenya"
            },
            "mombasa": {
                "temperature": 30,
                "condition": "Sunny",
                "humidity": 80,
                "wind_speed": 15,
                "location": "Mombasa, Kenya"
            },
            "kisumu": {
                "temperature": 26,
                "condition": "Light Rain",
                "humidity": 75,
                "wind_speed": 8,
                "location": "Kisumu, Kenya"
            }
        }
        
        location_key = location.lower().replace(" ", "")
        
        if location_key in weather_data:
            return weather_data[location_key]
        else:
            return {
                "temperature": 25,
                "condition": "Unknown",
                "humidity": 70,
                "wind_speed": 10,
                "location": location
            }
    except Exception as e:
        logger.error(f"Error in get_weather: {e}")
        return {"error": str(e)}

@tool("calculator", args_schema=CalculatorInput)
def calculator(expression: str) -> Dict[str, Any]:
    """
    Evaluates a mathematical expression and returns the result.
    """
    try:
        # For safety, we'll implement a simple calculator with basic operations
        # In a real application, use a safer evaluation method
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "expression": expression,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error in calculator: {e}")
        return {"error": f"Could not evaluate expression: {str(e)}"}

@tool("unit_converter", args_schema=ConversionInput)
def unit_converter(value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
    """
    Converts values between different units of measurement.
    """
    try:
        # Define conversion factors
        conversion_map = {
            # Length
            "meters_to_feet": 3.28084,
            "feet_to_meters": 0.3048,
            # Volume
            "liters_to_gallons": 0.264172,
            "gallons_to_liters": 3.78541,
            # Weight
            "kg_to_pounds": 2.20462,
            "pounds_to_kg": 0.453592,
            # Pressure
            "bar_to_psi": 14.5038,
            "psi_to_bar": 0.0689476,
        }
        
        # Create the conversion key
        conversion_key = f"{from_unit.lower()}_to_{to_unit.lower()}"
        
        if conversion_key in conversion_map:
            result = value * conversion_map[conversion_key]
            return {
                "original_value": value,
                "original_unit": from_unit,
                "converted_value": result,
                "target_unit": to_unit,
                "conversion_factor": conversion_map[conversion_key]
            }
        else:
            return {"error": f"Conversion from {from_unit} to {to_unit} is not supported."}
    except Exception as e:
        logger.error(f"Error in unit_converter: {e}")
        return {"error": str(e)}



@tool("analyse_lab_report", args_schema=AnalyseLabReportInput)
def analyse_lab_report(report: str) -> Dict[str, Any]:
    """
    Take a lab report and analyze it to parse the data into a nice formart that the AI can analyse
    """

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


