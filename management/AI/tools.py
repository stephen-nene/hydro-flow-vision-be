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



def format_customer_request_prompt(
    customer_request: Dict,
    guideline: Optional[List[Dict]] = None,
    ai_settings: Optional[Dict] = None
) -> Dict:
    """
    Formats the customer request and guideline into a readable string
    for the Mother Agent to use as context.
    """
    try:
        # --- Unpack ---
        # Extract request info
        request = customer_request.get("customer_request", {})
        guidelines = customer_request.get("guideline", [])
        
        location = request.get("location", "-")
        source = request.get("water_source", "-")
        usage = request.get("water_usage", "-")
        flow = request.get("daily_flow_rate", "-")
        
        budget_data = request.get("budget", {})
        budget = f"{budget_data.get('amount')} {budget_data.get('currency')}" if budget_data else "-"
        
        notes = request.get("notes", "-")

        # Water Parameters
        parameters = request.get("water_parameters", [])
        param_lines = [
            f"- {param['name']}: {param['value']} {param.get('unit', '')}".strip()
            for param in parameters
        ]

        # Guidelines
        guideline_lines = [
            f"- {g['name']}: {g['min_value']} - {g['max_value']} {g.get('unit', '')}".strip()
            for g in guidelines
        ]

            #  You are preparing a technical brief for a customer water treatment request.

            #  This summary will be used as the first step in an automated process where other AI models and tools will handle specific tasks such as RO sizing, treatment recommendations, and cost estimation.
            #  Your role is to:
            #  - **Analyze the provided lab report** and create a human-readable project initiation summary/prompt that will be used to initiate an agentic system for water purification.
            #  - **Do not recommend treatments** or suggest RO sizing, as these will be handled by other specialized tools later in the process.
            #  - **Focus on presenting key aspects** relevant to system sizing, pretreatment, and costing in a clear, accessible way for downstream tools.
        output = f"""
            📌 **Customer Request Summary**


            - **Location**: {location}
            - **Water Source**: {source}
            - **Usage Type**: {usage}
            - **Daily Flow Rate**: {flow} m³/day
            - **Budget**: {budget}
            - **Notes**: {notes}

            ### 🔬 Water Parameters:
            {chr(10).join(param_lines) or "- No parameters provided."}

            ### 📏 Guideline Reference:
            {chr(10).join(guideline_lines) or "- No guidelines provided."}
                """.strip()

        return {
            "formatted_prompt": output,
            "debug_data": {
                "num_parameters": len(param_lines),
                "num_guidelines": len(guideline_lines),
                "customer_usage": usage,  # Changed from customer_request["water_usage"] to usage
            }
        }

    except Exception as e:
        return {
            "formatted_prompt": "",
            "error": str(e)
        }




@tool("analyse_lab_report", args_schema=AnalyseLabReportInput)
def analyse_lab_report(report: str) -> Dict[str, Any]:
    """
    Analyzes a water lab report and extracts key parameters in structured format.
    """
    try:
        prompt = f"""
        Analyze this water lab report and extract key parameters in JSON format:
        {report}
        
        Return format:
        {{
            "parameters": [
                {{
                    "name": "parameter_name",
                    "value": number,
                    "unit": "measurement_unit",
                    "status": "within_limits|exceeds_limits"
                }}
            ],
            "summary": "brief_quality_assessment"
        }}
        """
        response = llm.invoke(prompt)
        return json.loads(response.content)
    except Exception as e:
        logger.error(f"Error analyzing lab report: {e}")
        return {"error": str(e)}

@tool("treatment_recommendation", args_schema=TreatmentRecommendationInput)
def treatment_recommendation(text: str) -> Dict[str, Any]:
    """
    Generates water treatment recommendations based on analyzed lab data.
    """
    try:
        prompt = f"""
        Based on this water analysis:
        {text}
        
        Recommend treatment steps with:
        - Required processes (filtration, disinfection, etc.)
        - Suggested equipment
        - Estimated costs
        - Implementation timeline
        
        Return as structured JSON.
        """
        response = llm.invoke(prompt)
        return response.content
        return json.loads(response.content)
    except Exception as e:
        logger.error(f"Error generating treatment recommendation: {e}")
        return {"error": str(e)}

@tool("ro_sizing", args_schema=ROSizingInput)
def ro_sizing(text: str) -> Dict[str, Any]:
    """
    Recommends RO system sizing based on water analysis and flow requirements.
    """
    try:
        prompt = f"""
        Based on water analysis and daily flow requirements:
        {text}
        
        Calculate RO system requirements:
        - Required membrane size
        - Pre-treatment needs
        - Pump specifications
        - Expected output quality
        
        Return as structured JSON.
        """
        response = llm.invoke(prompt)
        # return json.loads(response.content)
        return response.content
    except Exception as e:
        logger.error(f"Error calculating RO sizing: {e}")
        return {"error": str(e)}

@tool("quotation_generator2", args_schema=QuotationGeneratorInput)
def quotation_generator2(report: str) -> Dict[str, Any]:
    """
    Generates a detailed quotation based on analyzed lab report and RO sizing data.
    Includes equipment list, pricing, warranties, and payment terms.
    """
    try:
        # Step 1: Parse and validate input
        try:
            report_data = json.loads(report) if isinstance(report, str) else report
            if not isinstance(report_data, dict):
                raise ValueError("Report must be a JSON object or string")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in report")
        
        # Step 2: Generate quotation content using AI
        prompt = f"""
        Generate a professional water treatment quotation based on these specifications:
        {json.dumps(report_data, indent=2)}
        
        Include these sections:
        1. COMPANY HEADER (use fictional company 'AquaPure Solutions')
        2. PROJECT SUMMARY
        3. EQUIPMENT LIST (with model numbers, quantities, unit prices)
        4. TOTAL COST BREAKDOWN
        5. WARRANTY INFORMATION (standard 1 year warranty)
        6. PAYMENT TERMS (50% advance, 50% on completion)
        7. VALIDITY PERIOD (30 days)
        8. SIGNATURE LINES
        
        Format as markdown with clear section headings. Use Kenyan Shillings (KES) for all prices.
        """
        
        # Use both Gemini and fallback to NVIDIA if needed
        try:
            response = llm.invoke(prompt)  # Try Gemini first
            quotation_content = response.content
        except Exception as e:
            logger.warning(f"Gemini failed, trying NVIDIA: {str(e)}")
            response = llm2.invoke(prompt)
            quotation_content = response.content
        
        # Step 3: Add calculated pricing
        try:
            pricing_prompt = f"""
            Calculate realistic market prices in KES for this equipment list:
            {quotation_content}
            
            Return JSON with:
            - equipment_list (array with name, model, quantity, unit_price)
            - subtotal
            - taxes (16% VAT)
            - total_amount
            """
            pricing_data = json.loads(llm.invoke(pricing_prompt).content)
            
            # Merge pricing into quotation
            quotation_data = {
                "content": quotation_content,
                "pricing": pricing_data,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "currency": "KES",
                    "valid_until": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                }
            }
            return quotation_data
            
        except Exception as e:
            logger.error(f"Pricing calculation failed: {str(e)}")
            return {
                "content": quotation_content,
                "error": f"Generated content but pricing failed: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Quotation generation failed: {str(e)}")
        return {"error": f"Quotation generation failed: {str(e)}"}
    
@tool("quotation_generator", args_schema=QuotationGeneratorInput)
def quotation_generator(report: str) -> Dict[str, Any]:
    """
    Generates a complete quotation with PDF output based on analyzed lab report and RO sizing.
    """
    try:
        # Parse input
        report_data = json.loads(report) if isinstance(report, str) else report
        
        # Generate content using AI
        prompt = f"""Generate a detailed quotation including:
        - Equipment list with models and specifications
        - Pricing breakdown in KES
        - Installation costs
        - Maintenance package options
        
        Based on this data: {json.dumps(report_data, indent=2)}
        """
        
        ai_response = llm.invoke(prompt)
        quotation_content = ai_response.content
        
        # Extract structured data
        data_prompt = f"""Extract from this quotation:
        {quotation_content}
        
        Return JSON with:
        - client_name
        - project_summary
        - equipment_items (array with name, model, quantity, unit_price)
        - total_amount
        - timeline
        """
        
        structured_data = json.loads(llm.invoke(data_prompt).content)
        
        # Generate equipment table
        equipment_table = "| Item | Model | Qty | Unit Price | Total |\n|------|-------|-----|------------|-------|\n"
        for item in structured_data['equipment_items']:
            total = item['quantity'] * item['unit_price']
            equipment_table += f"| {item['name']} | {item['model']} | {item['quantity']} | KES {item['unit_price']:,} | KES {total:,} |\n"
        
        # Prepare PDF data
        pdf_data = {
            "client_name": structured_data.get('client_name', report_data.get('customer_name', 'Client')),
            "project_summary": structured_data.get('project_summary', 'Water Treatment System'),
            "equipment_table": equipment_table,
            "timeline": structured_data.get('timeline', '3-4 weeks'),
            "metadata": {
                "source_data": report_data,
                "generated_at": datetime.now().isoformat()
            }
        }
        
        # Generate PDF
        pdf_result = generate_quotation_pdf(pdf_data)
        # Save the PDF
        if 'pdf_base64' in pdf_result:
            with open('quotation.pdf', 'wb') as f:
                f.write(base64.b64decode(pdf_result['pdf_base64']))
        
        return {
            "quotation_id": pdf_result['quotation_id'],
            "pdf_base64": pdf_result['pdf_base64'],
            "text_content": quotation_content,
            "structured_data": structured_data,
            "metadata": pdf_data['metadata']
        }
        
    except Exception as e:
        logger.error(f"Quotation generation failed: {str(e)}")
        return {"error": str(e)}

@tool("proposal_generator", args_schema=ProposalGeneratorInput)
def proposal_generator(report: str) -> Dict[str, Any]:
    """
    Generates a comprehensive project proposal including technical specifications,
    implementation timeline, and cost breakdown based on water analysis and RO sizing.
    """
    try:
        # Step 1: Parse and validate input
        try:
            report_data = json.loads(report) if isinstance(report, str) else report
            if not isinstance(report_data, dict):
                raise ValueError("Report must be a JSON object or string")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in report")
        
        # Step 2: Generate proposal structure
        prompt = f"""
        Create a professional water treatment project proposal based on:
        {json.dumps(report_data, indent=2)}
        
        Required sections:
        1. COVER PAGE (project title, date, client name)
        2. EXECUTIVE SUMMARY
        3. CURRENT WATER QUALITY ANALYSIS
        4. PROPOSED SOLUTION (technology selection justification)
        5. SYSTEM DESIGN (process flow diagram description)
        6. EQUIPMENT SPECIFICATIONS (detailed with models)
        7. IMPLEMENTATION TIMELINE (Gantt chart description)
        8. COST BREAKDOWN (equipment, installation, maintenance)
        9. COMPANY PROFILE (brief background)
        10. TERMS & CONDITIONS
        
        Use markdown formatting with headings. Include technical details but keep it professional.
        """
        
        # Generate with fallback logic
        try:
            response = llm.invoke(prompt)
            proposal_content = response.content
        except Exception as e:
            logger.warning(f"Gemini failed, trying NVIDIA: {str(e)}")
            response = llm2.invoke(prompt)
            proposal_content = response.content
        
        # Step 3: Enhance with technical details
        try:
            tech_prompt = f"""
            Enhance these technical sections of a water treatment proposal:
            {proposal_content}
            
            Add:
            - Specific equipment performance specs
            - Detailed installation requirements
            - Maintenance schedule
            - Expected output water quality metrics
            
            Keep other sections unchanged.
            """
            enhanced_content = llm.invoke(tech_prompt).content
            
            return {
                "proposal": enhanced_content,
                "sections": {
                    "technical": True,
                    "financial": True,
                    "timeline": True
                },
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            
        except Exception as e:
            logger.warning(f"Technical enhancement failed, returning basic proposal: {str(e)}")
            return {
                "proposal": proposal_content,
                "sections": {
                    "technical": False,
                    "financial": True,
                    "timeline": True
                },
                "warning": f"Basic proposal generated but technical enhancement failed: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Proposal generation failed: {str(e)}")
        return {"error": f"Proposal generation failed: {str(e)}"}


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
    

# @tool("formart customer request", args_schema=FormatCustomerRequestInput)
@tool("format customer request")
def format_customer_request_prompt2(
    customer_request: Dict,
    guideline: Optional[List[Dict]] = None,
    ai_settings: Optional[Dict] = None
) -> Dict:
    """
    Generates a *self-contained* system prompt where the Mother Agent performs ALL checks 
    (parameter validation, usage matching) and follows explicit orchestration rules.
    """
    try:


        # --- RAW PROMPT (AI does all reasoning) ---
        raw_prompt = f"""
        **TASK**: Generate a *detailed* system data analysis with these data so that i can this to my ai mother agent
                 You are preparing a technical brief for a customer water treatment request.

             This summary will be used as the first step in an automated process where other AI models and tools will handle specific tasks such as RO sizing, treatment recommendations, and cost estimation.
             Your role is to:
             - **Analyze the provided lab report** and create a human-readable project initiation summary/prompt that will be used to initiate an agentic system for water purification.
             - **Do not recommend treatments** or suggest RO sizing, as these will be handled by other specialized tools later in the process.
             - **Focus on presenting key aspects** relevant to system sizing, pretreatment, and costing in a clear, accessible way for downstream tools.


        **GUIDELINES** (for the Mother Agent to use):
        ```python
        guidelines = {guideline}  # Raw guideline data
        ```

        **CUSTOMER REQUEST** (for the Mother Agent to analyze):
        ```python
        {{
            "location": "{customer_request['location']}",
            "water_source": "{customer_request['water_source']}",
            "water_usage": "{customer_request['water_usage']}",
            "parameters": {customer_request["water_parameters"]},
            "flow_rate": "{customer_request['daily_flow_rate']} m³/day"
        }}
        ```



          ```
        """

        # Generate the Mother Agent's prompt
        result = llm.invoke(raw_prompt)

        return {
            "formatted_prompt": result.content,
            "debug_data": {
                "guideline_provided": bool(guideline),
                "customer_usage": customer_request["water_usage"],
                # "guideline_usage": guideline["usage"] if guideline else None,
            }
        }

    except Exception as e:
        logger.error(f"Prompt generation failed: {str(e)}")
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

