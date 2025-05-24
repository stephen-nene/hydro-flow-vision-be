# register_water.py
# SPDX-FileCopyrightText: Copyright (c) 2024-2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union, Any
from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.config.base_config import FunctionBaseConfig
import json
import logging

logger = logging.getLogger(__name__)

class WaterAnalysisConfig(FunctionBaseConfig, name="water_analysis"):
    min_response_time: int = 5
    max_retries: int = 3
    temperature: float = 0.3
    max_tokens: int = 2048
    model_name: str = "meta/llama-3.1-70b-instruct"

class TreatmentDesignConfig(FunctionBaseConfig, name="treatment_design"):
    temperature: float = 0.2
    max_tokens: int = 3000
    model_name: str = "meta/llama-3.1-70b-instruct"

class SystemSizingConfig(FunctionBaseConfig, name="system_sizing"):
    temperature: float = 0.1
    max_tokens: int = 2500
    model_name: str = "meta/llama-3.1-70b-instruct"

class CostCalculationConfig(FunctionBaseConfig, name="cost_calculation"):
    temperature: float = 0.0
    max_tokens: int = 2000
    model_name: str = "meta/llama-3.1-70b-instruct"

# Data Models
class WaterParameter(BaseModel):
    name: str
    value: Optional[float]
    unit: Optional[str]
    guideline_min: Optional[float] = None
    guideline_max: Optional[float] = None

class GuidelineParameter(BaseModel):
    name: str
    unit: Optional[str]
    min_value: Optional[float]
    max_value: Optional[float]
    critical_level: Optional[str] = "standard"

class CustomerRequestInput(BaseModel):
    location: str
    water_source: str
    water_usage: str
    daily_flow_rate: int
    budget: Dict[str, Union[int, float, str]]
    water_parameters: List[WaterParameter]
    notes: Optional[str] = "No additional notes provided."
    priority_requirements: Optional[List[str]] = []

class ParameterViolation(BaseModel):
    parameter_name: str
    current_value: float
    limit_value: float
    violation_type: str  # "exceeds_max", "below_min"
    severity: str  # "critical", "major", "minor"
    health_risk: str
    treatment_required: str

class TreatmentSpecs(BaseModel):
    parameter_violations: List[ParameterViolation]
    required_treatments: List[str]
    treatment_priority: List[str]
    system_type: str
    feasibility_assessment: str
    cost_estimate_range: Dict[str, float]
    reasoning: str

class ROSystemSpecs(BaseModel):
    membrane_type: str
    membrane_count: int
    system_capacity: float
    recovery_rate: float
    pretreatment_requirements: List[str]
    post_treatment_requirements: List[str]
    estimated_cost: Dict[str, float]
    technical_reasoning: str

class SystemSizing(BaseModel):
    system_dimensions: Dict[str, float]
    power_requirements: Dict[str, float]
    space_requirements: str
    installation_complexity: str
    maintenance_schedule: List[str]
    sizing_reasoning: str

class QuotationOutput(BaseModel):
    line_items: List[Dict[str, Any]]
    subtotal: float
    taxes: float
    total_cost: float
    payment_terms: str
    validity_period: str
    budget_analysis: str
    recommendations: List[str]
    cost_reasoning: str

# System Messages for Each Tool
SYSTEM_MESSAGES = {
    "analyse_lab_report": """
    You are a water quality expert analyzing lab reports against water quality guidelines.
    
    Your role:
    1. Compare water parameters against applicable guidelines
    2. Identify violations and assess their severity
    3. Determine health risks and treatment requirements
    4. ALWAYS prioritize water safety over budget constraints
    5. Consider the intended water usage when assessing violations
    
    Critical Principles:
    - Water safety is NON-NEGOTIABLE
    - If budget is insufficient for safe treatment, clearly state this
    - Provide clear reasoning for each violation assessment
    - Consider synergistic effects between multiple parameter violations
    
    Output structured analysis with clear reasoning for each decision.
    """,
    
    "treatment_recommendation": """
    You are a water treatment system design engineer specializing in RO systems.
    
    Your role:
    1. Analyze parameter violations and design appropriate treatment systems
    2. Recommend RO membrane types and configurations
    3. Specify pretreatment and post-treatment requirements
    4. Assess technical feasibility and provide cost estimates
    5. PRIORITIZE effective treatment over cost considerations
    
    Design Principles:
    - Effective treatment is the primary goal
    - Budget constraints are secondary to safety
    - Consider long-term operational costs
    - Account for water source variability
    - Ensure system redundancy for critical applications
    
    Provide detailed technical reasoning for all recommendations.
    """,
    
    "ro_sizing": """
    You are a RO system sizing specialist with expertise in system optimization.
    
    Your role:
    1. Calculate optimal system dimensions and capacity
    2. Determine power and space requirements
    3. Assess installation complexity
    4. Develop maintenance schedules
    5. Optimize for efficiency while meeting performance requirements
    
    Sizing Principles:
    - Ensure adequate capacity with safety margins
    - Consider peak demand scenarios
    - Optimize for energy efficiency
    - Plan for future expansion if needed
    - Consider local installation constraints
    
    Provide comprehensive sizing analysis with clear technical reasoning.
    """,
    
    "quotation_generator": """
    You are a technical sales engineer creating detailed quotations for water treatment systems.
    
    Your role:
    1. Generate comprehensive cost breakdowns
    2. Analyze budget feasibility
    3. Provide alternative solutions if budget is insufficient
    4. Include all necessary components and services
    5. Be transparent about cost drivers
    
    Quotation Principles:
    - Transparency in all cost components
    - Clear explanation of why costs are necessary
    - If budget is insufficient, explain the risks of cheaper alternatives
    - Provide phased implementation options if applicable
    - Include long-term operational cost considerations
    
    Always explain your cost reasoning and provide budget analysis.
    """
}

@register_function(config_type=WaterAnalysisConfig)
async def analyse_lab_report(config: WaterAnalysisConfig, builder: Builder):
    """Analyzes water lab reports against guidelines using AI reasoning"""
    
    llm = await builder.get_llm()
    
    async def _analysis_fn(
        customer_request: dict,
        guideline: dict
    ) -> dict:
        
        # Prepare the analysis prompt
        analysis_prompt = f"""
        {SYSTEM_MESSAGES['analyse_lab_report']}
        
        CUSTOMER REQUEST:
        {json.dumps(customer_request, indent=2)}
        
        WATER QUALITY GUIDELINES:
        {json.dumps(guideline, indent=2)}
        
        ANALYSIS TASK:
        1. Compare each water parameter against the applicable guideline limits
        2. Identify violations and assess severity (critical/major/minor)
        3. Determine health risks for each violation
        4. Specify treatment requirements for each violation
        5. Consider the customer's budget vs. safety requirements
        6. Provide clear reasoning for your analysis
        
        IMPORTANT: If the customer's budget cannot support safe water treatment, clearly state this.
        Water safety must always be prioritized over cost considerations.
        
        Return your analysis in the following JSON format:
        {{
            "parameter_violations": [
                {{
                    "parameter_name": "string",
                    "current_value": float,
                    "limit_value": float,
                    "violation_type": "exceeds_max|below_min",
                    "severity": "critical|major|minor",
                    "health_risk": "detailed explanation",
                    "treatment_required": "specific treatment method"
                }}
            ],
            "required_treatments": ["list of required treatments"],
            "treatment_priority": ["prioritized list"],
            "system_type": "recommended system type",
            "feasibility_assessment": "budget vs requirements analysis",
            "cost_estimate_range": {{"min": float, "max": float}},
            "reasoning": "detailed explanation of analysis and decisions"
        }}
        """
        
        try:
            response = await llm.ainvoke(analysis_prompt)
            result = json.loads(response.content)
            
            # Validate and structure the response
            treatment_specs = TreatmentSpecs(**result)
            
            logger.info(f"Lab report analysis completed. Found {len(treatment_specs.parameter_violations)} violations.")
            
            return treatment_specs.dict()
            
        except Exception as e:
            logger.error(f"Error in lab report analysis: {str(e)}")
            # Return a safe fallback response
            return TreatmentSpecs(
                parameter_violations=[],
                required_treatments=["comprehensive_analysis_required"],
                treatment_priority=["safety_first"],
                system_type="comprehensive_ro_system",
                feasibility_assessment="Manual review required due to analysis error",
                cost_estimate_range={"min": 10000, "max": 50000},
                reasoning=f"Analysis error occurred: {str(e)}. Manual review recommended."
            ).dict()

    yield FunctionInfo.from_fn(
        _analysis_fn,
        description="AI-powered water lab report analysis with safety-first reasoning",
        input_model={
            "customer_request": dict,
            "guideline": dict
        },
        output_model=TreatmentSpecs
    )

@register_function(config_type=TreatmentDesignConfig)
async def treatment_recommendation(config: TreatmentDesignConfig, builder: Builder):
    """Generates intelligent treatment recommendations using AI reasoning"""
    
    llm = await builder.get_llm()
    
    async def _treatment_recommendation_fn(
        treatment_specs: dict
    ) -> dict:
        
        recommendation_prompt = f"""
        {SYSTEM_MESSAGES['treatment_recommendation']}
        
        PARAMETER VIOLATIONS AND REQUIREMENTS:
        {json.dumps(treatment_specs, indent=2)}
        
        DESIGN TASK:
        1. Design an optimal RO system configuration for the identified violations
        2. Specify membrane types, quantities, and arrangements
        3. Determine pretreatment requirements (sediment filters, carbon, etc.)
        4. Specify post-treatment needs (remineralization, pH adjustment, etc.)
        5. Calculate system capacity and recovery rates
        6. Estimate comprehensive costs
        7. Assess technical feasibility
        8. Provide detailed technical reasoning
        
        DESIGN PRIORITIES:
        - Effective treatment of all identified violations
        - System reliability and redundancy
        - Long-term operational efficiency
        - Maintenance accessibility
        
        Return your recommendation in the following JSON format:
        {{
            "membrane_type": "specific membrane recommendation",
            "membrane_count": integer,
            "system_capacity": float,
            "recovery_rate": float,
            "pretreatment_requirements": ["detailed list"],
            "post_treatment_requirements": ["detailed list"],
            "estimated_cost": {{
                "equipment": float,
                "installation": float,
                "annual_maintenance": float
            }},
            "technical_reasoning": "comprehensive explanation of design decisions and trade-offs"
        }}
        """
        
        try:
            response = await llm.ainvoke(recommendation_prompt)
            result = json.loads(response.content)
            
            ro_specs = ROSystemSpecs(**result)
            
            logger.info(f"Treatment recommendation generated for {ro_specs.membrane_type} system")
            
            return ro_specs.dict()
            
        except Exception as e:
            logger.error(f"Error in treatment recommendation: {str(e)}")
            return ROSystemSpecs(
                membrane_type="high_rejection_composite",
                membrane_count=4,
                system_capacity=1000.0,
                recovery_rate=75.0,
                pretreatment_requirements=["sediment_filter", "carbon_filter", "antiscalant"],
                post_treatment_requirements=["remineralization", "pH_adjustment"],
                estimated_cost={"equipment": 25000, "installation": 5000, "annual_maintenance": 3000},
                technical_reasoning=f"Default recommendation due to analysis error: {str(e)}"
            ).dict()

    yield FunctionInfo.from_fn(
        _treatment_recommendation_fn,
        description="AI-powered RO system design with comprehensive technical reasoning",
        input_model=TreatmentSpecs,
        output_model=ROSystemSpecs
    )

@register_function(config_type=SystemSizingConfig)
async def ro_sizing(config: SystemSizingConfig, builder: Builder):
    """Generates intelligent system sizing with AI reasoning"""
    
    llm = await builder.get_llm()
    
    async def _ro_sizing_fn(
        ro_system_specs: dict
    ) -> dict:
        
        sizing_prompt = f"""
        {SYSTEM_MESSAGES['ro_sizing']}
        
        RO SYSTEM SPECIFICATIONS:
        {json.dumps(ro_system_specs, indent=2)}
        
        SIZING TASK:
        1. Calculate optimal system dimensions (length, width, height)
        2. Determine power requirements (electrical load, backup power)
        3. Assess space requirements and layout considerations
        4. Evaluate installation complexity and requirements
        5. Develop comprehensive maintenance schedule
        6. Consider future expansion possibilities
        7. Optimize for energy efficiency
        
        SIZING CONSIDERATIONS:
        - Safety margins for capacity and power
        - Accessibility for maintenance
        - Local electrical and plumbing codes
        - Environmental conditions
        - Operational efficiency
        
        Return your sizing analysis in the following JSON format:
        {{
            "system_dimensions": {{
                "length_m": float,
                "width_m": float,
                "height_m": float,
                "total_footprint_m2": float
            }},
            "power_requirements": {{
                "operating_kw": float,
                "peak_kw": float,
                "daily_kwh": float,
                "backup_power_needed": boolean
            }},
            "space_requirements": "detailed space and layout requirements",
            "installation_complexity": "assessment of installation challenges",
            "maintenance_schedule": ["detailed maintenance tasks and frequencies"],
            "sizing_reasoning": "comprehensive explanation of sizing decisions and optimizations"
        }}
        """
        
        try:
            response = await llm.ainvoke(sizing_prompt)
            result = json.loads(response.content)
            
            sizing_specs = SystemSizing(**result)
            
            logger.info(f"System sizing completed: {sizing_specs.system_dimensions}")
            
            return sizing_specs.dict()
            
        except Exception as e:
            logger.error(f"Error in system sizing: {str(e)}")
            return SystemSizing(
                system_dimensions={
                    "length_m": 3.0,
                    "width_m": 2.0,
                    "height_m": 2.5,
                    "total_footprint_m2": 6.0
                },
                power_requirements={
                    "operating_kw": 5.0,
                    "peak_kw": 7.5,
                    "daily_kwh": 120.0,
                    "backup_power_needed": True
                },
                space_requirements="Standard industrial installation space",
                installation_complexity="Moderate - requires professional installation",
                maintenance_schedule=["Weekly: Check pressures", "Monthly: Replace filters", "Quarterly: System inspection"],
                sizing_reasoning=f"Default sizing due to analysis error: {str(e)}"
            ).dict()

    yield FunctionInfo.from_fn(
        _ro_sizing_fn,
        description="AI-powered system sizing with optimization reasoning",
        input_model=ROSystemSpecs,
        output_model=SystemSizing
    )

@register_function(config_type=CostCalculationConfig)
async def quotation_generator(config: CostCalculationConfig, builder: Builder):
    """Generates intelligent quotations with budget analysis and AI reasoning"""
    
    llm = await builder.get_llm()
    
    async def _quotation_generator_fn(
        ro_system_specs: dict,
        ro_sizing: dict,
        customer_budget: dict
    ) -> dict:
        
        quotation_prompt = f"""
        {SYSTEM_MESSAGES['quotation_generator']}
        
        RO SYSTEM SPECIFICATIONS:
        {json.dumps(ro_system_specs, indent=2)}
        
        SYSTEM SIZING:
        {json.dumps(ro_sizing, indent=2)}
        
        CUSTOMER BUDGET:
        {json.dumps(customer_budget, indent=2)}
        
        QUOTATION TASK:
        1. Generate detailed line-item costs for all components
        2. Include equipment, installation, and commissioning costs
        3. Calculate taxes and total project cost
        4. Analyze budget feasibility
        5. Provide alternative solutions if over budget
        6. Include operational cost projections
        7. Specify payment terms and validity
        8. Provide clear cost reasoning
        
        COSTING PRINCIPLES:
        - Transparency in all cost components
        - Realistic market pricing
        - Include all necessary components
        - Account for local installation factors
        - Consider long-term value
        
        BUDGET ANALYSIS:
        - If over budget, explain why costs are necessary
        - Suggest phased implementation if applicable
        - Warn about risks of cheaper alternatives
        - Prioritize safety-critical components
        
        Return your quotation in the following JSON format:
        {{
            "line_items": [
                {{
                    "item": "string",
                    "description": "string",
                    "quantity": integer,
                    "unit_price": float,
                    "total_price": float,
                    "category": "equipment|installation|service"
                }}
            ],
            "subtotal": float,
            "taxes": float,
            "total_cost": float,
            "payment_terms": "detailed payment terms",
            "validity_period": "quotation validity period",
            "budget_analysis": "detailed analysis of budget vs requirements",
            "recommendations": ["list of recommendations"],
            "cost_reasoning": "comprehensive explanation of costing decisions and budget analysis"
        }}
        """
        
        try:
            response = await llm.ainvoke(quotation_prompt)
            result = json.loads(response.content)
            
            quotation = QuotationOutput(**result)
            
            logger.info(f"Quotation generated: Total cost ${quotation.total_cost:,.2f}")
            
            return quotation.dict()
            
        except Exception as e:
            logger.error(f"Error in quotation generation: {str(e)}")
            return QuotationOutput(
                line_items=[
                    {
                        "item": "RO System Package",
                        "description": "Complete RO system with installation",
                        "quantity": 1,
                        "unit_price": 30000.0,
                        "total_price": 30000.0,
                        "category": "equipment"
                    }
                ],
                subtotal=30000.0,
                taxes=3000.0,
                total_cost=33000.0,
                payment_terms="50% down, 50% on completion",
                validity_period="30 days",
                budget_analysis="Default quotation due to analysis error",
                recommendations=["Manual review required"],
                cost_reasoning=f"Default quotation due to analysis error: {str(e)}"
            ).dict()

    yield FunctionInfo.from_fn(
        _quotation_generator_fn,
        description="AI-powered quotation generation with comprehensive budget analysis",
        input_model={
            "ro_system_specs": dict,
            "ro_sizing": dict,
            "customer_budget": dict
        },
        output_model=QuotationOutput
    )