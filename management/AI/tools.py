from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import requests
from requests.auth import HTTPBasicAuth

import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")



class PumpSearchInput(BaseModel):
    model_name: str = Field(description="The model name of the Davis & Shirtliff pump, e.g., DDP 60")


@tool("get_pump_from_erp", args_schema=PumpSearchInput, return_direct=True)
def get_pump_from_erp(model_name: str):
    """
    Retrieves pump details for a given Davis & Shirtliff pump model from the Business Central ERP system.
    """
    try:
        url = os.getenv("BC_ERP_URL")
        username = os.getenv("BC_ERP_USERNAME")
        password = os.getenv("BC_ERP_PASSWORD")

        if not all([url, username, password]):
            return {"error": "Missing ERP credentials or URL in environment variables."}

        params = {
            "$filter": "Gen_Prod_Posting_Group eq 'CAT08'"
        }
        auth = HTTPBasicAuth(username, password)

        response = requests.get(url, params=params, auth=auth)
        response.raise_for_status()

        pumps = response.json().get("value", [])

        # Find matching model
        for pump in pumps:
            pump_no = pump.get("No")
            pump_description = pump.get("Description", "").lower()
            pump_model = pump.get("Product_Model", "").lower()

            if model_name.lower() == pump_no.lower():
                return {
                    "Model Number": pump_no,
                    "Product_Model": pump.get("Product_Model"),
                    "Description": pump_description,
                    "Inventory": pump.get("Inventory"),
                    "Retail_Price": pump.get("Retail_Price")
                }
            if model_name.lower() in pump_description or model_name.lower() in pump_model or model_name.lower() in pump_no.lower():
                 return {
                    "Model Number": pump_no,
                    "Product_Model": pump.get("Product_Model"),
                    "Description": pump_description,
                    "Inventory": pump.get("Inventory"),
                    "Retail_Price": pump.get("Retail_Price")
                }

        return {"error": f"No pump found with model name matching '{model_name}'. Please check the model name and try again."}

    except Exception as e:
        return {"error": str(e)}
    