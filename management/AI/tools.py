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
from datetime import datetime,timedelta
import base64

from langchain_google_genai import ChatGoogleGenerativeAI

from ..management.pdfs.gen import generate_quotation_pdf

# Initialize the LLM
llm2 = ChatOpenAI(
    model="deepseek-ai/deepseek-r1",
    # model='meta/llama-4-scout-17b-16e-instruct',
    # model="google/gemma-3-27b-it",
    temperature=0.3,  
    max_tokens=1024,
    timeout=None,
#   top_p=0.7,
    max_retries=2,
    api_key=config('NVIDIA_SECRET_KEY'),
    base_url="https://integrate.api.nvidia.com/v1",

)

# Create LLM class
llm = ChatGoogleGenerativeAI(
    # model= "gemini-2.0-flash",
    model= 'gemini-1.5-pro',
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
# class AgentState(TypedDict):
#     """The state of the agent."""
#     messages: Annotated[Sequence[BaseMessage], add_messages]
#     steps: int

# # Define input schemas for tools
# class PumpSearchInput(BaseModel):
#     model_name: str = Field(description="The model name of the pump to search for")

# class WaterParameter(BaseModel):
#     name: str
#     value: Optional[float]
#     unit: Optional[str]


# class GuidelineParameter(BaseModel):
#     name: str
#     unit: Optional[str]
#     min_value: Optional[float]
#     max_value: Optional[float]


# class CustomerRequestInput(BaseModel):
#     location: str
#     water_source: str
#     water_usage: str
#     daily_flow_rate: int
#     budget: Dict[str, Union[int, float, str]]
#     water_parameters: List[WaterParameter]
#     notes: Optional[str] = "No additional notes provided."

# class AnalyseLabReportInput(BaseModel):
#     customer_request: CustomerRequestInput
#     guideline: Optional[List[GuidelineParameter]]











# ----------------------
# 1. SCHEMA DEFINITIONS
# ----------------------
class AgentState(TypedDict):
    """The state of the agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    steps: int

class WaterAnalysisInput(BaseModel):
    customer_request: dict = Field(..., description="Contains water parameters, usage, and flow rate")
    guideline: dict = Field(..., description="Water quality standards to compare against")

class WaterAnalysisOutput(BaseModel):
    treatment_specs: dict = Field(..., description="Required treatments and priority level")
    parameter_violations: list = Field(..., description="List of violated parameters with details")

class TreatmentRecommendationInput(BaseModel):
    treatment_specs: dict = Field(..., description="Output from water analysis")
    customer_request: dict = Field(..., description="Usage and technical requirements")

class ROSizingInput(BaseModel):
    treatment_specs: dict = Field(..., description="Recommended treatment system specs")
    customer_request: dict = Field(..., description="Flow rate and location details")

class QuotationInput(BaseModel):
    system_specs: dict = Field(..., description="Finalized system specifications")
    customer_request: dict = Field(..., description="Contact and location info")

class ProposalInput(BaseModel):
    technical_specs: dict = Field(..., description="All technical specifications")
    cost_estimate: dict = Field(..., description="Pricing breakdown")

# ----------------------
# 2. TOOL IMPLEMENTATIONS
# ----------------------

def llm_fallback(prompt: str, schema: BaseModel) -> dict:
    """Enhanced LLM executor with robust error handling"""
    for llm_client in [llm, llm2]:  # Try both LLMs
        try:
            response = llm_client.invoke(prompt).content
            print(response)
            
            # Validate response is non-empty JSON
            if not response.strip():
                raise ValueError("Empty response")
                
            parsed = json.loads(response)
            validated = schema.model_validate(parsed)
            return validated.model_dump()
            
        except Exception as e:
            logger.warning(f"{llm_client._llm_type} failed: {str(e)}")
            continue
    
    # If all LLMs fail
    raise ValueError(f"All LLMs failed to process request. Last error: {str(e)}")

@tool(args_schema=WaterAnalysisInput)
def analyse_lab_report2(customer_request: dict, guideline: dict) -> dict:
    """Analyzes water parameters against guidelines"""
    input_data = {
        "customer_request": customer_request,
        "guideline": guideline
    }
    prompt = f"""Analyze water quality:
        Input: {json.dumps(input_data)}
        Output format: {WaterAnalysisOutput.model_json_schema()}

        Rules:
        1. Ignore budget constraints
        2. Strictly follow guideline limits
        3. Return JSON matching the schema"""
    
    result = llm.invoke(prompt)
    return WaterAnalysisOutput(
        treatment_specs={}, 
        parameter_violations=result
    ).model_dump()
    # return result.dict()

@tool(args_schema=WaterAnalysisInput)
def analyse_lab_report(customer_request: dict, guideline: dict) -> dict:
    """Analyzes water parameters against guidelines"""
    violations = []

    for param, customer_value in customer_request.items():
        guideline_value = guideline.get(param)
        if not guideline_value:
            continue

        min_val = guideline_value.get("min")
        max_val = guideline_value.get("max")
        unit = guideline_value.get("unit", "")

        if min_val is not None and customer_value < min_val:
            violations.append({
                "parameter": param,
                "value": customer_value,
                "violation": "below minimum",
                "guideline_range": f"{min_val} - {max_val} {unit}"
            })
        elif max_val is not None and customer_value > max_val:
            violations.append({
                "parameter": param,
                "value": customer_value,
                "violation": "above maximum",
                "guideline_range": f"{min_val} - {max_val} {unit}"
            })

    return {
        "parameter_violations": violations
    }





@tool(args_schema=TreatmentRecommendationInput)
def treatment_recommendation(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Recommends treatment systems based on parameter violations and customer needs"""
    parameter_violations = input_data.get("parameter_violations", {})
    customer_request = input_data.get("customer_request", {})
    prompt = f"""
You are a water treatment system design expert. Based on the data below, recommend:

1. An RO system specification (type, capacity, and key components)
2. A pretreatment plan (filtration method and required chemical adjustments)

Input Data:
- Treatment specs (violated parameters): {json.dumps(parameter_violations, indent=2)}
- Customer request (usage, daily flow rate,  etc.): {json.dumps(customer_request, indent=2)}
Write only the final Markdown output. Do not include JSON, commentary, or additional explanations. 
"""
# Return JSON matching this exact format:
# {json.dumps({
#     "ro_system_specs": {"type": "string", "capacity": "string", "components": ["string"]},
#     "pretreatment": {"filtration": "string", "chemical_adjustments": ["string"]}
# }, indent=2)}
    
    result = llm_fallback(prompt, str)  # Expecting a string (Markdown)
    return {"treatment_specs": result}


@tool(args_schema=ROSizingInput)
def ro_sizing(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates RO system requirements"""
    prompt = f"""
        You are an RO system sizing expert. Based on the customer input below, calculate and summarize the following in Markdown:

        - Number of membranes required
        - Recommended tank capacity
        - Pump specifications (type and power)

        ### Customer Input:
        ```json
        {json.dumps(input_data, indent=2)}
        ```

        ### Output format (Markdown):
        ```markdown
        ## RO Sizing

        - **Membranes Required**: X
        - **Tank Capacity**: X Liters
        - **Pump Specs**:
        - Type: X
        - Power: X
        ```

        Write only the Markdown output. No JSON or additional explanations.
        """
    result = llm_fallback(prompt, str)
    return {"ro_sizing": result}

@tool(args_schema=QuotationInput)
def quotation_generator(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a cost estimate based on system specs and treatment plan"""

    prompt = f"""
You are a project cost estimator. Using the information below, produce:

- base_price: Total equipment cost (float)
- components: List of items with their individual costs
- total_cost: Sum of all costs (float)

Inputs:
### Input Data:
```json
{json.dumps(input_data, indent=2)}
```

Return JSON exactly with markdown to allow you to be creative  as:
{json.dumps({
    "base_price": 0.0,
    "components": [{"name": "string", "cost": 0.0}],
    "total_cost": 0.0
}, indent=2)}
"""
    result = llm_fallback(prompt, str)
    return {"quotation_generator": result}

@tool(args_schema=ProposalInput)
def proposal_generator(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a final customer proposal combining all details"""
    # quotation = input_data.get("quotation", {})
    # ro_system_specs = input_data.get("ro_system_specs", {})
    # pretreatment = input_data.get("pretreatment", {})
    # customer_request = input_data.get("customer_request", {})

# - Quotation details: {json.dumps(quotation, indent=2)}
# - RO system specs: {json.dumps(ro_system_specs, indent=2)}
# - Pretreatment plan: {json.dumps(pretreatment, indent=2)}
# - Customer request: {json.dumps(customer_request, indent=2)}
    prompt = f"""
You are a technical consultant preparing a proposal document. Using the data below, create a JSON proposal containing:

1. system_overview: A concise summary string
2. technical_specs: {{ "flow_rate": "string", "treatment_stages": ["string"] }}
3. cost_breakdown: {{ "equipment": float, "installation": float }}

Inputs:
{json.dumps(input_data, indent=2)}

Return ONLY the JSON matching this schema.
{json.dumps({
    "system_overview": "string",
    "technical_specs": {"flow_rate": "string", "treatment_stages": ["string"]},
    "cost_breakdown": {"equipment": 0.0, "installation": 0.0}
}, indent=2)}
"""
    
    result = llm_fallback(prompt, str)
    return {"proposal_generator": result}


# ----------------------
# 3. STRUCTURED OUTPUT GUARANTEE
# ----------------------

class ToolError(BaseModel):
    error: str = Field(..., description="Error description")
    tool: str = Field(..., description="Tool that failed")

def structured_tool_wrapper(func):
    """Ensures tools return valid JSON or error"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Tool failed: {str(e)}")
            return {"success": False, "error": ToolError(
                error=str(e),
                tool=func.__name__
            ).model_dump()}
    return wrapper

# Apply to all tools
tools = [
    structured_tool_wrapper(analyse_lab_report),
    structured_tool_wrapper(treatment_recommendation),
    structured_tool_wrapper(ro_sizing),
    structured_tool_wrapper(quotation_generator),
    structured_tool_wrapper(proposal_generator)
]










# result = analyse_lab_report.invoke({
#     "customer_request": {
#         "water_parameters": {"pH": 8.2, "TDS": 1200},
#         "water_usage": "residential"
#     },
#     "guideline": {
#         "pH": {"min": 6.5, "max": 8.5},
#         "TDS": {"max": 1000}
#     }
# })

# if result['success']:
#     print("Treatment specs:", result['data']['treatment_specs'])
# else:
#     print("Error in", result['error']['tool'])






















# @tool("analyse_lab_report", args_schema=AnalyseLabReportInput)
# def analyse_lab_report(
#     customer_request: Dict,
#     guideline: Optional[List[Dict]] = None,
#     ai_settings: Optional[Dict] = None
# ) -> Dict:
#     """
#     Formats the customer request and guideline into a readable string
#     for the Mother Agent to use as context.
#     """
#     try:
#         # --- Unpack ---
#         # Extract request info
#         request = customer_request.get("customer_request", {})
#         guidelines = customer_request.get("guideline", [])
        
#         location = request.get("location", "-")
#         source = request.get("water_source", "-")
#         usage = request.get("water_usage", "-")
#         flow = request.get("daily_flow_rate", "-")
        
#         budget_data = request.get("budget", {})
#         budget = f"{budget_data.get('amount')} {budget_data.get('currency')}" if budget_data else "-"
        
#         notes = request.get("notes", "-")

#         # Water Parameters
#         parameters = request.get("water_parameters", [])
#         param_lines = [
#             f"- {param['name']}: {param['value']} {param.get('unit', '')}".strip()
#             for param in parameters
#         ]

#         # Guidelines
#         guideline_lines = [
#             f"- {g['name']}: {g['min_value']} - {g['max_value']} {g.get('unit', '')}".strip()
#             for g in guidelines
#         ]

#             #  You are preparing a technical brief for a customer water treatment request.

#             #  This summary will be used as the first step in an automated process where other AI models and tools will handle specific tasks such as RO sizing, treatment recommendations, and cost estimation.
#             #  Your role is to:
#             #  - **Analyze the provided lab report** and create a human-readable project initiation summary/prompt that will be used to initiate an agentic system for water purification.
#             #  - **Do not recommend treatments** or suggest RO sizing, as these will be handled by other specialized tools later in the process.
#             #  - **Focus on presenting key aspects** relevant to system sizing, pretreatment, and costing in a clear, accessible way for downstream tools.
#         output = f"""
#             📌 **Customer Request Summary**


#             - **Location**: {location}
#             - **Water Source**: {source}
#             - **Usage Type**: {usage}
#             - **Daily Flow Rate**: {flow} m³/day
#             - **Budget**: {budget}
#             - **Notes**: {notes}

#             ### 🔬 Water Parameters:
#             {chr(10).join(param_lines) or "- No parameters provided."}

#             ### 📏 Guideline Reference:
#             {chr(10).join(guideline_lines) or "- No guidelines provided."}
#                 """.strip()

#         return {
#             "formatted_prompt": output,
#             "debug_data": {
#                 "num_parameters": len(param_lines),
#                 "num_guidelines": len(guideline_lines),
#                 "customer_usage": usage,  # Changed from customer_request["water_usage"] to usage
#             }
#         }

#     except Exception as e:
#         return {
#             "formatted_prompt": "",
#             "error": str(e)
#         }



# @tool("treatment_recommendation", args_schema=TreatmentRecommendationInput)
# def treatment_recommendation(text: str) -> Dict[str, Any]:
#     """
#     Generates water treatment recommendations based on analyzed lab data.
#     """
#     try:
#         result = format_customer_request_prompt(text)
#         prompt = f"""
#         Based on this water analysis:
#         {result}
        
#         Recommend treatment steps with:
#         - Required processes (filtration, disinfection, etc.)
#         - Suggested equipment
#         - Implementation timeline
        
#         Return as structured JSON.
#         """
#         response = llm.invoke(prompt)
#         return response.content
#         return json.loads(response.content)
#     except Exception as e:
#         logger.error(f"Error generating treatment recommendation: {e}")
#         return {"error": str(e)}

# @tool("ro_sizing", args_schema=ROSizingInput)
# def ro_sizing(text: str) -> Dict[str, Any]:
#     """
#     Recommends RO system sizing based on water analysis and flow requirements.
#     """
#     try:
#         prompt = f"""
#         Based on water analysis and daily flow requirements:
#         {text}
        
#         Calculate RO system requirements:
#         - Required membrane size
#         - Pre-treatment needs
#         - Pump specifications
#         - Expected output quality
        
#         Return as structured JSON.
#         """
#         response = llm.invoke(prompt)
#         # return json.loads(response.content)
#         return response.content
#     except Exception as e:
#         logger.error(f"Error calculating RO sizing: {e}")
#         return {"error": str(e)}

# @tool("quotation_generator", args_schema=QuotationGeneratorInput)
# def quotation_generator(report: str) -> Dict[str, Any]:
#     """
#     Generates a detailed quotation based on analyzed lab report and RO sizing data.
#     Includes equipment list, pricing, warranties, and payment terms.
#     """
#     try:
#         # Step 1: Parse and validate input
#         try:
#             report_data = json.loads(report) if isinstance(report, str) else report
#             if not isinstance(report_data, dict):
#                 raise ValueError("Report must be a JSON object or string")
#         except json.JSONDecodeError:
#             raise ValueError("Invalid JSON format in report")
        
#         # Step 2: Generate quotation content using AI
#         prompt = f"""
#         Generate a professional water treatment quotation based on these specifications:
#         {json.dumps(report_data, indent=2)}
        
#         Include these sections:
#         1. COMPANY HEADER (use fictional company 'AquaPure Solutions')
#         2. PROJECT SUMMARY
#         3. EQUIPMENT LIST (with model numbers, quantities, unit prices)
#         4. TOTAL COST BREAKDOWN
#         5. WARRANTY INFORMATION (standard 1 year warranty)
#         6. PAYMENT TERMS (50% advance, 50% on completion)
#         7. VALIDITY PERIOD (30 days)
#         8. SIGNATURE LINES
        
#         Format as markdown with clear section headings. Use Kenyan Shillings (KES) for all prices.
#         """
        
#         # Use both Gemini and fallback to NVIDIA if needed
#         try:
#             response = llm.invoke(prompt)  # Try Gemini first
#             quotation_content = response.content
#         except Exception as e:
#             logger.warning(f"Gemini failed, trying NVIDIA: {str(e)}")
#             response = llm2.invoke(prompt)
#             quotation_content = response.content
        
#         # Step 3: Add calculated pricing
#         try:
#             pricing_prompt = f"""
#             Calculate realistic market prices in KES for this equipment list:
#             {quotation_content}
            
#             Return JSON with:
#             - equipment_list (array with name, model, quantity, unit_price)
#             - subtotal
#             - taxes (16% VAT)
#             - total_amount
#             """
#             pricing_data = json.loads(llm.invoke(pricing_prompt).content)
            
#             # Merge pricing into quotation
#             quotation_data = {
#                 "content": quotation_content,
#                 "pricing": pricing_data,
#                 "metadata": {
#                     "generated_at": datetime.now().isoformat(),
#                     "currency": "KES",
#                     "valid_until": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
#                 }
#             }
#             return quotation_data
            
#         except Exception as e:
#             logger.error(f"Pricing calculation failed: {str(e)}")
#             return {
#                 "content": quotation_content,
#                 "error": f"Generated content but pricing failed: {str(e)}"
#             }
            
#     except Exception as e:
#         logger.error(f"Quotation generation failed: {str(e)}")
#         return {"error": f"Quotation generation failed: {str(e)}"}
    
# @tool("proposal_generator", args_schema=ProposalGeneratorInput)
# def proposal_generator(report: str) -> Dict[str, Any]:
#     """
#     Generates a comprehensive project proposal including technical specifications,
#     implementation timeline, and cost breakdown based on water analysis and RO sizing.
#     """
#     try:
#         # Step 1: Parse and validate input
#         try:
#             report_data = json.loads(report) if isinstance(report, str) else report
#             if not isinstance(report_data, dict):
#                 raise ValueError("Report must be a JSON object or string")
#         except json.JSONDecodeError:
#             raise ValueError("Invalid JSON format in report")
        
#         # Step 2: Generate proposal structure
#         prompt = f"""
#         Create a professional water treatment project proposal based on:
#         {json.dumps(report_data, indent=2)}
        
#         Required sections:
#         1. COVER PAGE (project title, date, client name)
#         2. EXECUTIVE SUMMARY
#         3. CURRENT WATER QUALITY ANALYSIS
#         4. PROPOSED SOLUTION (technology selection justification)
#         5. SYSTEM DESIGN (process flow diagram description)
#         6. EQUIPMENT SPECIFICATIONS (detailed with models)
#         7. IMPLEMENTATION TIMELINE (Gantt chart description)
#         8. COST BREAKDOWN (equipment, installation, maintenance)
#         9. COMPANY PROFILE (brief background)
#         10. TERMS & CONDITIONS
        
#         Use markdown formatting with headings. Include technical details but keep it professional.
#         """
        
#         # Generate with fallback logic
#         try:
#             response = llm.invoke(prompt)
#             proposal_content = response.content
#         except Exception as e:
#             logger.warning(f"Gemini failed, trying NVIDIA: {str(e)}")
#             response = llm2.invoke(prompt)
#             proposal_content = response.content
        
#         # Step 3: Enhance with technical details
#         try:
#             tech_prompt = f"""
#             Enhance these technical sections of a water treatment proposal:
#             {proposal_content}
            
#             Add:
#             - Specific equipment performance specs
#             - Detailed installation requirements
#             - Maintenance schedule
#             - Expected output water quality metrics
            
#             Keep other sections unchanged.
#             """
#             enhanced_content = llm.invoke(tech_prompt).content
            
#             return {
#                 "proposal": enhanced_content,
#                 "sections": {
#                     "technical": True,
#                     "financial": True,
#                     "timeline": True
#                 },
#                 "metadata": {
#                     "generated_at": datetime.now().isoformat(),
#                     "version": "1.0"
#                 }
#             }
            
#         except Exception as e:
#             logger.warning(f"Technical enhancement failed, returning basic proposal: {str(e)}")
#             return {
#                 "proposal": proposal_content,
#                 "sections": {
#                     "technical": False,
#                     "financial": True,
#                     "timeline": True
#                 },
#                 "warning": f"Basic proposal generated but technical enhancement failed: {str(e)}"
#             }
            
#     except Exception as e:
#         logger.error(f"Proposal generation failed: {str(e)}")
#         return {"error": f"Proposal generation failed: {str(e)}"}


# Define tools

BC_API_BASE_URL="https://bctest.dayliff.com:7048/BC160/ODataV4/Company('KENYA')/ItemsAPI"
BC_API_USERNAME="davisapi"
BC_API_PASSWORD="zheghH5w631+AQ8GkKK6AMTEHGaPHP23aK8okWWQmGE="

def get_product_details(no: str) -> Dict:
    """Fetch comprehensive product details"""
    params = {"$filter": f"No eq '{no}'"}
    try:
        response = requests.get(
            BC_API_BASE_URL,
            params=params,
            auth=HTTPBasicAuth(BC_API_USERNAME, BC_API_PASSWORD)
        )
        response.raise_for_status()
        data = response.json()
        
        if 'value' in data and data['value']:
            item = data['value'][0]
            return {
                'no': item.get('No', ''),
                'inventory': int(item.get('Inventory', 0)),
                'unit_price': float(item.get('Unit_Price', 0)),
                'description': item.get('Description', ''),
                'item_category_code': item.get('Item_Category_Code', ''),
                'product_model': item.get('Product_Model', ''),
                'specifications': item.get('Technical_Specifications', ''),
                'warranty': item.get('Warranty_Period', '')
            }
        return {}
    except requests.RequestException as e:
        str.error(f"Error fetching product details: {str(e)}")
        return {}
    


# @tool("get_pump_details", args_schema=PumpSearchInput)
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
    

