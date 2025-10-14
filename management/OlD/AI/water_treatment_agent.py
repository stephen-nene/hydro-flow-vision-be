# water_treatment_agent.py
# SPDX-FileCopyrightText: Copyright (c) 2024-2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.config.base_config import FunctionBaseConfig
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WaterTreatmentAgentConfig(FunctionBaseConfig, name="water_treatment_agent"):
    """Main agent configuration"""
    guideline_url: str = "https://your-water-standards.com"
    component_db_url: str = "https://ro-components-db.com"
    max_retries: int = 3
    validation_strict: bool = True
    temperature: float = 0.2
    model_name: str = "meta/llama-3.1-70b-instruct"

class WaterTreatmentInput(BaseModel):
    """Main input for the water treatment agent"""
    customer_request_id: str = Field(..., description="UUID of the customer request")
    guideline_id: Optional[str] = Field(None, description="Optional guideline ID")
    override_usage_check: bool = Field(False, description="Override usage compatibility check")
    ai_settings: Dict[str, Any] = Field(default_factory=dict, description="AI processing settings")
    customer_request: Dict[str, Any] = Field(..., description="Customer request data from DB")
    guideline: Optional[Dict[str, Any]] = Field(None, description="Guideline data from DB")

class WaterTreatmentOutput(BaseModel):
    """Main output from the water treatment agent"""
    request_id: str
    analysis_results: Dict[str, Any]
    treatment_recommendation: Dict[str, Any]
    system_sizing: Dict[str, Any]
    quotation: Dict[str, Any]
    overall_assessment: str
    budget_feasibility: str
    recommendations: List[str]
    processing_metadata: Dict[str, Any]
    timestamp: str

# Main Agent System Message
AGENT_SYSTEM_MESSAGE = """
You are the Water Treatment System AI Agent, orchestrating a comprehensive analysis and recommendation system.

Your role is to:
1. Coordinate the analysis of water quality data against applicable guidelines
2. Ensure all treatment recommendations prioritize water safety
3. Provide comprehensive system design and cost analysis
4. Offer clear guidance when budget constraints conflict with safety requirements
5. Generate actionable recommendations for customers

Core Principles:
- Water safety is ALWAYS the top priority
- Be transparent about costs and their necessity
- Provide clear reasoning for all recommendations
- Offer alternatives when budget is a constraint
- Ensure all analysis is technically sound and practical

You will coordinate multiple specialized tools to provide a complete water treatment solution.
"""

@register_function(config_type=WaterTreatmentAgentConfig)
async def water_treatment_agent(config: WaterTreatmentAgentConfig, builder: Builder):
    """Main water treatment agent that orchestrates the entire workflow"""
    
    # Get the LLM for orchestration
    llm = await builder.get_llm()
    
    # Register all the specialized tools
    try:
        from register_water import (
            analyse_lab_report, 
            treatment_recommendation, 
            ro_sizing, 
            quotation_generator
        )
        
        analysis_tool = await builder.register_tool(analyse_lab_report)
        treatment_tool = await builder.register_tool(treatment_recommendation)
        sizing_tool = await builder.register_tool(ro_sizing)
        quotation_tool = await builder.register_tool(quotation_generator)
        
        logger.info("All water treatment tools registered successfully")
        
    except Exception as e:
        logger.error(f"Error registering tools: {str(e)}")
        raise

    async def _water_treatment_workflow(
        customer_request_id: str,
        customer_request: dict,
        guideline: dict = None,
        override_usage_check: bool = False,
        ai_settings: dict = None
    ) -> dict:
        """Main workflow orchestrating all water treatment analysis"""
        
        start_time = datetime.now()
        processing_metadata = {
            "start_time": start_time.isoformat(),
            "steps_completed": [],
            "errors": [],
            "ai_settings": ai_settings or {}
        }
        
        try:
            # Step 1: Orchestration Planning
            orchestration_prompt = f"""
            {AGENT_SYSTEM_MESSAGE}
            
            WORKFLOW ORCHESTRATION TASK:
            
            Customer Request ID: {customer_request_id}
            Customer Request: {json.dumps(customer_request, indent=2)}
            Guideline: {json.dumps(guideline, indent=2) if guideline else "No specific guideline provided"}
            Override Usage Check: {override_usage_check}
            
            Plan the workflow execution:
            1. Assess the completeness of input data
            2. Identify any data validation issues
            3. Plan the execution sequence
            4. Anticipate potential issues
            
            Provide a brief analysis of the workflow readiness and any concerns.
            """
            
            orchestration_response = await llm.ainvoke(orchestration_prompt)
            logger.info(f"Workflow orchestration planned: {orchestration_response.content[:200]}...")
            
            # Step 1: Lab Report Analysis
            logger.info(f"Step 1: Starting lab report analysis for request {customer_request_id}")
            
            analysis_input = {
                "customer_request": customer_request,
                "guideline": guideline or {}
            }
            
            analysis_results = await analysis_tool(analysis_input)
            processing_metadata["steps_completed"].append("lab_analysis")
            
            logger.info(f"Lab analysis completed. Found {len(analysis_results.get('parameter_violations', []))} violations")
            
            # Step 2: Treatment Recommendation
            logger.info("Step 2: Generating treatment recommendations")
            
            treatment_results = await treatment_tool(analysis_results)
            processing_metadata["steps_completed"].append("treatment_recommendation")
            
            logger.info(f"Treatment recommendation completed: {treatment_results.get('membrane_type', 'Unknown')} system")
            
            # Step 3: System Sizing
            logger.info("Step 3: Performing system sizing")
            
            sizing_results = await sizing_tool(treatment_results)
            processing_metadata["steps_completed"].append("system_sizing")
            
            logger.info(f"System sizing completed: {sizing_results.get('system_dimensions', {}).get('total_footprint_m2', 'Unknown')} m²")
            
            # Step 4: Quotation Generation
            logger.info("Step 4: Generating quotation")
            
            quotation_input = {
                "ro_system_specs": treatment_results,
                "ro_sizing": sizing_results,
                "customer_budget": customer_request.get("budget", {})
            }
            
            quotation_results = await quotation_tool(quotation_input)
            processing_metadata["steps_completed"].append("quotation_generation")
            
            logger.info(f"Quotation completed: ${quotation_results.get('total_cost', 0):,.2f}")
            
            # Step 5: Overall Assessment and Recommendations
            logger.info("Step 5: Generating overall assessment")
            
            assessment_prompt = f"""
            {AGENT_SYSTEM_MESSAGE}
            
            OVERALL ASSESSMENT TASK:
            
            Based on the complete analysis, provide an overall assessment and recommendations:
            
            ANALYSIS RESULTS:
            {json.dumps(analysis_results, indent=2)}
            
            TREATMENT RECOMMENDATION:
            {json.dumps(treatment_results, indent=2)}
            
            SYSTEM SIZING:
            {json.dumps(sizing_results, indent=2)}
            
            QUOTATION:
            {json.dumps(quotation_results, indent=2)}
            
            CUSTOMER REQUEST:
            {json.dumps(customer_request, indent=2)}
            
            Provide:
            1. Overall water quality assessment
            2. Treatment necessity and urgency
            3. Budget feasibility analysis
            4. Priority recommendations
            5. Risk assessment if treatment is delayed
            6. Alternative solutions if budget is insufficient
            
            Format your response as:
            {{
                "overall_assessment": "comprehensive summary",
                "budget_feasibility": "detailed budget analysis",
                "priority_recommendations": ["list of prioritized recommendations"],
                "risk_assessment": "assessment of risks if treatment is delayed",
                "alternative_solutions": ["list of alternative approaches if budget is tight"]
            }}
            """
            
            assessment_response = await llm.ainvoke(assessment_prompt)
            assessment_data = json.loads(assessment_response.content)
            
            processing_metadata["end_time"] = datetime.now().isoformat()
            processing_metadata["total_duration_seconds"] = (
                datetime.now() - start_time
            ).total_seconds()
            
            # Compile final results
            final_results = WaterTreatmentOutput(
                request_id=customer_request_id,
                analysis_results=analysis_results,
                treatment_recommendation=treatment_results,
                system_sizing=sizing_results,
                quotation=quotation_results,
                overall_assessment=assessment_data.get("overall_assessment", ""),
                budget_feasibility=assessment_data.get("budget_feasibility", ""),
                recommendations=assessment_data.get("priority_recommendations", []),
                processing_metadata=processing_metadata,
                timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"Water treatment workflow completed successfully for request {customer_request_id}")
            
            return final_results.dict()
            
        except Exception as e:
            error_msg = f"Error in water treatment workflow: {str(e)}"
            logger.error(error_msg)
            processing_metadata["errors"].append(error_msg)
            processing_metadata["end_time"] = datetime.now().isoformat()
            
            # Return error response
            return {
                "request_id": customer_request_id,
                "error": error_msg,
                "processing_metadata": processing_metadata,
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }

    yield FunctionInfo.from_fn(
        _water_treatment_workflow,
        description="Complete AI-powered water treatment analysis and recommendation system",
        input_model=WaterTreatmentInput,
        output_model=WaterTreatmentOutput
    )

# Alternative React Agent Implementation
@register_function()
async def water_treatment_react_agent(builder: Builder):
    """React-style agent for water treatment workflow"""
    
    from aiq.agents.react_agent import ReactAgent
    from aiq.tools.tool import Tool
    
    # Register tools for React agent
    tools = []
    
    # Analysis Tool
    analysis_tool_def = Tool(
        name="analyse_lab_report",
        description="Analyzes water parameters against guidelines to identify violations and treatment needs",
        func=analyse_lab_report
    )
    tools.append(analysis_tool_def)
    
    # Treatment Tool
    treatment_tool_def = Tool(
        name="treatment_recommendation", 
        description="Generates RO system recommendations based on parameter violations",
        func=treatment_recommendation
    )
    tools.append(treatment_tool_def)
    
    # Sizing Tool
    sizing_tool_def = Tool(
        name="ro_sizing",
        description="Calculates optimal system dimensions and requirements",
        func=ro_sizing
    )
    tools.append(sizing_tool_def)
    
    # Quotation Tool
    quotation_tool_def = Tool(
        name="quotation_generator",
        description="Generates comprehensive cost quotations with budget analysis", 
        func=quotation_generator
    )
    tools.append(quotation_tool_def)
    
    # Create React Agent
    react_agent = ReactAgent(
        tools=tools,
        llm=await builder.get_llm(),
        system_message=f"""
        {AGENT_SYSTEM_MESSAGE}
        
        You have access to the following tools for water treatment analysis:
        
        1. analyse_lab_report: Analyzes water quality against guidelines
        2. treatment_recommendation: Designs RO treatment systems  
        3. ro_sizing: Calculates system dimensions and requirements
        4. quotation_generator: Creates cost quotations and budget analysis
        
        WORKFLOW PROCESS:
        1. Start with analyse_lab_report using customer_request and guideline data
        2. Use treatment_recommendation with the analysis results
        3. Apply ro_sizing to the treatment recommendations
        4. Generate quotation_generator with all previous results
        5. Provide final assessment and recommendations
        
        CRITICAL REMINDERS:
        - Always prioritize water safety over cost considerations
        - Be transparent about budget constraints vs. safety requirements
        - Provide clear reasoning for all recommendations
        - If budget is insufficient for safe treatment, clearly explain the risks
        """,
        max_iterations=10,
        verbose=True
    )
    
    async def _react_workflow(input_data: dict) -> dict:
        """React agent workflow for water treatment"""
        
        workflow_prompt = f"""
        Analyze the following water treatment request using the available tools:
        
        Customer Request: {json.dumps(input_data.get('customer_request', {}), indent=2)}
        Guideline: {json.dumps(input_data.get('guideline', {}), indent=2)}
        
        Complete the full analysis workflow:
        1. Analyze the lab report against guidelines
        2. Generate treatment recommendations
        3. Calculate system sizing
        4. Create quotation with budget analysis
        5. Provide final assessment
        
        Ensure water safety is prioritized throughout the analysis.
        """
        
        result = await react_agent.run(workflow_prompt)
        return {"react_agent_result": result}
    
    yield FunctionInfo.from_fn(
        _react_workflow,
        description="React-style water treatment agent with tool orchestration",
        input_model=dict,
        output_model=dict
    )