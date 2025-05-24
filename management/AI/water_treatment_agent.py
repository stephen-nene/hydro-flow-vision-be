# File: water_treatment_agent.py
from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from pydantic import BaseModel

class WaterTreatmentConfig(BaseModel):
    guideline_url: str = "https://your-water-standards.com"
    component_db_url: str = "https://ro-components-db.com"

@register_function()
async def water_treatment_agent(builder: Builder):
    # 1. Register your tools
    analysis_tool = await builder.register_tool(analyse_lab_report)
    treatment_tool = await builder.register_tool(treatment_recommendation)
    
    # 2. Create agentic workflow
    async def run_analysis(input_data: dict):
        # Structured data flow
        analysis = await analysis_tool(input_data)
        treatment = await treatment_tool(analysis)
        return treatment
        
    yield FunctionInfo.from_fn(run_analysis, 
        description="End-to-end water treatment recommendation system")