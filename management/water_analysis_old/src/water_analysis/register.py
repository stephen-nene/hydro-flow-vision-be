# register.py
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from langchain_nvidia_ai_endpoints import ChatNVIDIA

class WaterAnalysisConfig(FunctionBaseConfig, name="water_analysis"):
    llm_model: str = Field(default="meta/llama3-70b-instruct", description="NVIDIA LLM model to use")
    safety_margin: float = Field(default=0.2, description="Safety margin for parameter violations")

class TreatmentSpecs(BaseModel):
    violations: Dict[str, Dict[str, float]] = Field(..., description="Parameter violation details")
    required_treatments: List[str] = Field(..., description="Required treatment processes")
    safety_concerns: List[str] = Field(default_factory=list)
    budget_impact: Optional[str] = None

class ROSystemSpecs(BaseModel):
    membranes: int
    pump_hp: float
    tank_size: float
    pretreatment: List[str]
    estimated_cost: Dict[str, float]

class Quotation(BaseModel):
    essential_components: List[Dict[str, float]]
    optional_upgrades: List[Dict[str, float]]
    maintenance_plan: Dict[str, float]
    total_cost: Dict[str, float]
    budget_analysis: str

@register_function(config_type=WaterAnalysisConfig)
async def analyse_lab_report(config: WaterAnalysisConfig, builder: Builder):
    """Structured comparison without LLM"""
    async def _analysis_fn(customer_request: dict, guideline: dict) -> dict:
        violations = {}
        for param in guideline["parameters"]:
            customer_val = next(
                (p["value"] for p in customer_request["water_lab_reports"][0]["parameters"] 
                if p["name"] == param["name"]), None
            )
            
            if customer_val is not None:
                if param.get("min_value") and customer_val < param["min_value"] * (1 - config.safety_margin):
                    violations[param["name"]] = {
                        "value": customer_val,
                        "min_allowed": param["min_value"],
                        "type": "below_min"
                    }
                elif param.get("max_value") and customer_val > param["max_value"] * (1 + config.safety_margin):
                    violations[param["name"]] = {
                        "value": customer_val,
                        "max_allowed": param["max_value"],
                        "type": "above_max"
                    }
        
        return TreatmentSpecs(
            violations=violations,
            required_treatments=[],
            safety_concerns=[]
        ).dict()

    yield FunctionInfo.from_fn(_analysis_fn)

@register_function(config_type=WaterAnalysisConfig)
async def treatment_recommendation(config: WaterAnalysisConfig, builder: Builder):
    llm = ChatNVIDIA(model=config.llm_model, temperature=0.2)
    
    async def _treatment_fn(specs: dict) -> dict:
        prompt = f"""Analyze these water parameter violations and recommend treatments:
        
        Violations: {specs['violations']}
        Customer Budget: {specs.get('budget', 'Unspecified')}
        Water Usage: {specs.get('water_usage', 'Unknown')}
        
        Rules:
        1. Always prioritize health/safety violations first
        2. Recommend RO only if TDS > 500ppm
        3. Include disinfection if microbial risk exists
        4. Provide budget impact assessment
        
        Output JSON with: required_treatments, safety_concerns, budget_impact"""
        
        response = await llm.ainvoke(prompt)
        return response.content

    yield FunctionInfo.from_fn(_treatment_fn, output_model=TreatmentSpecs)

@register_function(config_type=WaterAnalysisConfig)
async def ro_sizing(config: WaterAnalysisConfig, builder: Builder):
    llm = ChatNVIDIA(model=config.llm_model, temperature=0.1)
    
    async def _sizing_fn(specs: dict) -> dict:
        prompt = f"""Design RO system for:
        Daily Flow: {specs['daily_flow_rate']} m3/day
        Required Treatments: {specs['required_treatments']}
        Site Constraints: {specs.get('site_location', 'Standard')}
        
        Calculate:
        - Number of membranes (4" elements)
        - Pump HP required
        - Tank size (m3)
        - Pretreatment needed
        
        Return JSON with: membranes, pump_hp, tank_size, pretreatment, estimated_cost"""
        
        response = await llm.ainvoke(prompt)
        return response.content

    yield FunctionInfo.from_fn(_sizing_fn, output_model=ROSystemSpecs)

@register_function(config_type=WaterAnalysisConfig)
async def quotation_generator(config: WaterAnalysisConfig, builder: Builder):

    llm = ChatNVIDIA(model=config.llm_model, temperature=0.3)
    
    async def _quotation_fn(system_specs: dict, customer_request: dict) -> dict:
        prompt = f"""Generate quotation for:
        System: {system_specs}
        Customer Budget: {customer_request['budget']}
        Currency: {customer_request['budget'].get('currency', 'USD')}
        
        Include:
        1. Essential safety components (non-negotiable)
        2. Optional upgrades
        3. 3-year maintenance plan
        4. Budget comparison analysis
        
        Return JSON with: essential_components, optional_upgrades, maintenance_plan, total_cost, budget_analysis"""
        
        response = await llm.ainvoke(prompt)
        return response.content

    yield FunctionInfo.from_fn(_quotation_fn, output_model=Quotation)


@register_function()
async def water_treatment_agent(builder: Builder) -> AsyncGenerator[FunctionInfo, None]:
    # Register all tools first
    analysis_tool = await builder.register_tool(analyse_lab_report)
    treatment_tool = await builder.register_tool(treatment_recommendation)
    sizing_tool = await builder.register_tool(ro_sizing)
    quote_tool = await builder.register_tool(quotation_generator)
    
    async def agent_fn(input_data: dict) -> dict:
        analysis = await analysis_tool(input_data)
        treatment = await treatment_tool(analysis)
        sizing = await sizing_tool(treatment)
        quote = await quote_tool({**sizing, **input_data})
        return quote
    
    try:
        yield FunctionInfo.from_fn(agent_fn)
    finally:
        logger.debug("Agent workflow cleaned up")