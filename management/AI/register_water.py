# register_water.py - Enhanced with AI Reasoning Capabilities

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union, Any
from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
import asyncio
import json

# Base configuration with NVIDIA AI capabilities
class WaterAnalysisConfig(BaseModel):
    name: str = "water_analysis"
    min_response_time: int = 5
    max_retries: int = 3
    ai_model: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    enable_reasoning: bool = True
    reasoning_temperature: float = 0.7
    max_reasoning_tokens: int = 2048

# Data Models
class WaterParameter(BaseModel):
    name: str
    value: Optional[float]
    unit: Optional[str]
    status: Optional[str] = None  # "compliant", "violation", "warning"

class GuidelineParameter(BaseModel):
    name: str
    unit: Optional[str]
    min_value: Optional[float]
    max_value: Optional[float]
    priority: str = "medium"  # "critical", "high", "medium", "low"

class CustomerRequestInput(BaseModel):
    location: str
    water_source: str
    water_usage: str
    daily_flow_rate: int
    budget: Dict[str, Union[int, float, str]]
    water_parameters: List[WaterParameter]
    notes: Optional[str] = "No additional notes provided."

class AnalysisReasoningOutput(BaseModel):
    reasoning: str
    compliance_assessment: Dict[str, Any]
    priority_violations: List[str]
    budget_feasibility: str
    recommended_actions: List[str]

class TreatmentSpecs(BaseModel):
    parameters: Dict[str, Any] = Field(..., description="Parameter violation details")
    required_treatments: List[str]
    reasoning: Optional[str] = None
    confidence_score: Optional[float] = None
    cost_estimate_range: Optional[Dict[str, float]] = None

class TreatmentRecommendation(BaseModel):
    primary_treatment: str
    secondary_treatments: List[str]
    treatment_sequence: List[Dict[str, Any]]
    reasoning: str
    expected_outcomes: Dict[str, str]
    maintenance_requirements: List[str]
    confidence_score: float

class ROSizingOutput(BaseModel):
    membrane_type: str
    membrane_count: int
    system_capacity: float
    recovery_rate: float
    pressure_requirements: Dict[str, float]
    sizing_reasoning: str
    performance_predictions: Dict[str, Any]
    maintenance_schedule: List[str]

class QuotationOutput(BaseModel):
    total_cost: float
    cost_breakdown: Dict[str, float]
    financing_options: List[Dict[str, Any]]
    roi_analysis: Dict[str, Any]
    quotation_reasoning: str
    risk_assessment: str
    alternatives: List[Dict[str, Any]]

# AI Reasoning Helper Class
class AIReasoningEngine:
    def __init__(self, config: WaterAnalysisConfig):
        self.config = config
        self.model = config.ai_model
        
    async def reason_through_analysis(self, customer_request: dict, guidelines: dict, 
                                    analysis_results: dict) -> AnalysisReasoningOutput:
        """Use AI to reason through lab report analysis"""
        
        system_prompt = """You are an expert water treatment engineer with deep knowledge of water quality standards and treatment technologies. 
        
        Your task is to analyze water quality data against guidelines and provide reasoned recommendations.
        
        CRITICAL PRIORITIES:
        1. Water safety and compliance ALWAYS comes first
        2. If budget constraints conflict with water safety, prioritize safety and explain alternatives
        3. Consider customer usage patterns and location-specific factors
        4. Provide clear reasoning for all recommendations
        
        Analyze the provided data and give your expert reasoning."""
        
        user_prompt = f"""
        Customer Request: {json.dumps(customer_request, indent=2)}
        Guidelines: {json.dumps(guidelines, indent=2)}
        Analysis Results: {json.dumps(analysis_results, indent=2)}
        
        Please provide:
        1. Clear reasoning about compliance status
        2. Priority violations that must be addressed
        3. Budget feasibility assessment
        4. Recommended immediate actions
        """
        
        # Simulate AI reasoning call (replace with actual NVIDIA AI toolkit call)
        reasoning_response = await self._call_nvidia_ai(system_prompt, user_prompt)
        
        return AnalysisReasoningOutput(
            reasoning=reasoning_response.get("reasoning", ""),
            compliance_assessment=reasoning_response.get("compliance", {}),
            priority_violations=reasoning_response.get("violations", []),
            budget_feasibility=reasoning_response.get("budget_assessment", ""),
            recommended_actions=reasoning_response.get("actions", [])
        )
    
    async def reason_through_treatment(self, treatment_specs: dict, 
                                     customer_context: dict) -> TreatmentRecommendation:
        """Use AI to reason through treatment recommendations"""
        
        system_prompt = """You are a water treatment system designer with expertise in selecting and sequencing treatment technologies.
        
        Your role is to design optimal treatment sequences that:
        1. Address all water quality violations effectively
        2. Consider operational efficiency and maintenance
        3. Balance performance with cost considerations
        4. Ensure long-term system reliability
        
        Think through the treatment design systematically."""
        
        user_prompt = f"""
        Treatment Requirements: {json.dumps(treatment_specs, indent=2)}
        Customer Context: {json.dumps(customer_context, indent=2)}
        
        Design the optimal treatment system with clear reasoning for:
        1. Primary treatment selection
        2. Treatment sequence and staging
        3. Expected performance outcomes
        4. Maintenance considerations
        """
        
        reasoning_response = await self._call_nvidia_ai(system_prompt, user_prompt)
        
        return TreatmentRecommendation(
            primary_treatment=reasoning_response.get("primary_treatment", ""),
            secondary_treatments=reasoning_response.get("secondary_treatments", []),
            treatment_sequence=reasoning_response.get("sequence", []),
            reasoning=reasoning_response.get("reasoning", ""),
            expected_outcomes=reasoning_response.get("outcomes", {}),
            maintenance_requirements=reasoning_response.get("maintenance", []),
            confidence_score=reasoning_response.get("confidence", 0.8)
        )
    
    async def reason_through_ro_sizing(self, treatment_specs: dict, 
                                     flow_requirements: dict) -> ROSizingOutput:
        """Use AI to reason through RO system sizing"""
        
        system_prompt = """You are an RO system design engineer with expertise in membrane selection and system sizing.
        
        Your expertise includes:
        1. Membrane technology selection based on water chemistry
        2. System capacity and recovery optimization
        3. Operating pressure and energy efficiency
        4. Maintenance scheduling and lifecycle management
        
        Provide detailed sizing analysis with engineering reasoning."""
        
        user_prompt = f"""
        Treatment Specifications: {json.dumps(treatment_specs, indent=2)}
        Flow Requirements: {json.dumps(flow_requirements, indent=2)}
        
        Design the RO system with reasoning for:
        1. Membrane selection and configuration
        2. System capacity and staging
        3. Operating parameters optimization
        4. Performance predictions and maintenance
        """
        
        reasoning_response = await self._call_nvidia_ai(system_prompt, user_prompt)
        
        return ROSizingOutput(
            membrane_type=reasoning_response.get("membrane_type", ""),
            membrane_count=reasoning_response.get("membrane_count", 1),
            system_capacity=reasoning_response.get("capacity", 0.0),
            recovery_rate=reasoning_response.get("recovery_rate", 0.75),
            pressure_requirements=reasoning_response.get("pressure", {}),
            sizing_reasoning=reasoning_response.get("reasoning", ""),
            performance_predictions=reasoning_response.get("performance", {}),
            maintenance_schedule=reasoning_response.get("maintenance", [])
        )
    
    async def reason_through_quotation(self, system_specs: dict, 
                                     customer_budget: dict) -> QuotationOutput:
        """Use AI to reason through quotation generation"""
        
        system_prompt = """You are a water treatment systems sales engineer with expertise in cost estimation and financial analysis.
        
        Your responsibilities include:
        1. Accurate cost estimation for treatment systems
        2. Financial analysis and ROI calculations
        3. Risk assessment and mitigation strategies
        4. Alternative solution development for budget constraints
        
        Always prioritize water safety while finding economically viable solutions."""
        
        user_prompt = f"""
        System Specifications: {json.dumps(system_specs, indent=2)}
        Customer Budget: {json.dumps(customer_budget, indent=2)}
        
        Generate a comprehensive quotation with:
        1. Detailed cost breakdown and justification
        2. ROI analysis and payback period
        3. Risk assessment and mitigation
        4. Alternative options if budget is insufficient
        """
        
        reasoning_response = await self._call_nvidia_ai(system_prompt, user_prompt)
        
        return QuotationOutput(
            total_cost=reasoning_response.get("total_cost", 0.0),
            cost_breakdown=reasoning_response.get("cost_breakdown", {}),
            financing_options=reasoning_response.get("financing", []),
            roi_analysis=reasoning_response.get("roi", {}),
            quotation_reasoning=reasoning_response.get("reasoning", ""),
            risk_assessment=reasoning_response.get("risks", ""),
            alternatives=reasoning_response.get("alternatives", [])
        )
    
    async def _call_nvidia_ai(self, system_prompt: str, user_prompt: str) -> dict:
        """Make actual call to NVIDIA AI model"""
        # This would be replaced with actual NVIDIA AI toolkit integration
        # For now, returning structured mock response
        
        # Example integration with NVIDIA AI:
        # from nvidia_ai_toolkit import AIQToolkit
        # toolkit = AIQToolkit(model=self.model)
        # response = await toolkit.generate(
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_prompt}
        #     ],
        #     temperature=self.config.reasoning_temperature,
        #     max_tokens=self.config.max_reasoning_tokens
        # )
        # return response.parsed_output
        
        return {
            "reasoning": "AI-generated reasoning would appear here",
            "confidence": 0.85,
            "primary_treatment": "Reverse Osmosis",
            "secondary_treatments": ["Pre-filtration", "Post-treatment"],
            "violations": ["High TDS", "Excessive hardness"],
            "budget_assessment": "Feasible with phased implementation",
            "actions": ["Immediate pre-treatment", "RO system installation"]
        }

# Enhanced Tool Registrations
@register_function(config_type=WaterAnalysisConfig)
async def analyse_lab_report(config: WaterAnalysisConfig, builder: Builder):
    """Enhanced lab report analysis with AI reasoning"""
    
    ai_engine = AIReasoningEngine(config)
    
    async def _analysis_fn(customer_request: dict, guideline: dict) -> dict:
        # Basic compliance checking
        analysis_results = {}
        violations = []
        
        # Check each parameter against guidelines
        for param in customer_request.get("water_parameters", []):
            param_name = param["name"]
            param_value = param.get("value")
            
            # Find corresponding guideline
            guideline_param = next(
                (g for g in guideline if g["name"] == param_name), 
                None
            )
            
            if guideline_param and param_value is not None:
                min_val = guideline_param.get("min_value")
                max_val = guideline_param.get("max_value")
                
                violation = False
                if min_val and param_value < min_val:
                    violation = True
                if max_val and param_value > max_val:
                    violation = True
                    
                if violation:
                    violations.append(param_name)
                    
                analysis_results[param_name] = {
                    "value": param_value,
                    "compliant": not violation,
                    "guideline": guideline_param
                }
        
        # Use AI to reason through the analysis
        if config.enable_reasoning:
            ai_reasoning = await ai_engine.reason_through_analysis(
                customer_request, guideline, analysis_results
            )
            
            return TreatmentSpecs(
                parameters=analysis_results,
                required_treatments=ai_reasoning.recommended_actions,
                reasoning=ai_reasoning.reasoning,
                confidence_score=0.9
            ).dict()
        else:
            # Fallback to basic analysis
            return TreatmentSpecs(
                parameters=analysis_results,
                required_treatments=violations
            ).dict()
    
    yield FunctionInfo.from_fn(
        _analysis_fn,
        description="Analyze lab reports against water quality guidelines with AI reasoning",
        input_model={"customer_request": dict, "guideline": dict},
        output_model=TreatmentSpecs
    )

@register_function(config_type=WaterAnalysisConfig)
async def treatment_recommendation(config: WaterAnalysisConfig, builder: Builder):
    """AI-enhanced treatment recommendation system"""
    
    ai_engine = AIReasoningEngine(config)
    
    async def _treatment_recommendation_fn(treatment_specs: dict, customer_context: dict = None) -> dict:
        
        if config.enable_reasoning and customer_context:
            # Use AI to generate comprehensive treatment recommendations
            ai_recommendation = await ai_engine.reason_through_treatment(
                treatment_specs, customer_context
            )
            return ai_recommendation.dict()
        else:
            # Basic rule-based recommendations
            violations = treatment_specs.get("required_treatments", [])
            basic_treatments = []
            
            if "High TDS" in violations or "Salinity" in violations:
                basic_treatments.append("Reverse Osmosis")
            if "Hardness" in violations:
                basic_treatments.append("Water Softening")
            if "Turbidity" in violations:
                basic_treatments.append("Sediment Filtration")
                
            return {
                "primary_treatment": basic_treatments[0] if basic_treatments else "Basic Filtration",
                "secondary_treatments": basic_treatments[1:],
                "reasoning": "Rule-based treatment selection"
            }
    
    yield FunctionInfo.from_fn(
        _treatment_recommendation_fn,
        description="Generate treatment recommendations with AI reasoning",
        input_model={"treatment_specs": dict, "customer_context": dict},
        output_model=TreatmentRecommendation
    )

@register_function(config_type=WaterAnalysisConfig)
async def ro_sizing(config: WaterAnalysisConfig, builder: Builder):
    """AI-enhanced RO system sizing"""
    
    ai_engine = AIReasoningEngine(config)
    
    async def _ro_sizing_fn(treatment_specs: dict, flow_requirements: dict = None) -> dict:
        
        if config.enable_reasoning:
            ai_sizing = await ai_engine.reason_through_ro_sizing(
                treatment_specs, flow_requirements or {}
            )
            return ai_sizing.dict()
        else:
            # Basic sizing calculations
            daily_flow = flow_requirements.get("daily_flow_rate", 1000) if flow_requirements else 1000
            
            return {
                "membrane_type": "Standard RO",
                "membrane_count": max(1, daily_flow // 1000),
                "system_capacity": daily_flow * 1.2,  # 20% safety factor
                "recovery_rate": 0.75,
                "sizing_reasoning": "Basic flow-based sizing"
            }
    
    yield FunctionInfo.from_fn(
        _ro_sizing_fn,
        description="Size RO systems with AI-driven engineering analysis",
        input_model={"treatment_specs": dict, "flow_requirements": dict},
        output_model=ROSizingOutput
    )

@register_function(config_type=WaterAnalysisConfig)
async def quotation_generator(config: WaterAnalysisConfig, builder: Builder):
    """AI-enhanced quotation generation with budget analysis"""
    
    ai_engine = AIReasoningEngine(config)
    
    async def _quotation_generator_fn(system_specs: dict, customer_budget: dict = None) -> dict:
        
        if config.enable_reasoning and customer_budget:
            ai_quotation = await ai_engine.reason_through_quotation(
                system_specs, customer_budget
            )
            return ai_quotation.dict()
        else:
            # Basic cost estimation
            base_cost = 10000  # Basic system cost
            treatment_multiplier = len(system_specs.get("required_treatments", [])) * 0.5
            total_cost = base_cost * (1 + treatment_multiplier)
            
            return {
                "total_cost": total_cost,
                "cost_breakdown": {
                    "equipment": total_cost * 0.7,
                    "installation": total_cost * 0.2,
                    "warranty": total_cost * 0.1
                },
                "quotation_reasoning": "Basic cost calculation"
            }
    
    yield FunctionInfo.from_fn(
        _quotation_generator_fn,
        description="Generate detailed quotations with AI-powered cost analysis",
        input_model={"system_specs": dict, "customer_budget": dict},
        output_model=QuotationOutput
    )

# Main orchestration tool
@register_function(config_type=WaterAnalysisConfig)
async def water_treatment_agent(config: WaterAnalysisConfig, builder: Builder):
    """Main orchestration agent with AI reasoning at each step"""
    
    async def _orchestrate_workflow(input_data: dict) -> dict:
        """
        Orchestrate the complete water treatment workflow with AI reasoning
        """
        
        # Extract components from input
        customer_request = input_data.get("customer_request", {})
        guidelines = input_data.get("guidelines", [])
        
        results = {"workflow_steps": []}
        
        try:
            # Step 1: Analyze lab report
            analysis_tool = await builder.get_tool("analyse_lab_report")
            analysis_result = await analysis_tool({
                "customer_request": customer_request,
                "guideline": guidelines
            })
            results["analysis"] = analysis_result
            results["workflow_steps"].append("Lab analysis completed with AI reasoning")
            
            # Step 2: Generate treatment recommendations
            treatment_tool = await builder.get_tool("treatment_recommendation")
            treatment_result = await treatment_tool({
                "treatment_specs": analysis_result,
                "customer_context": customer_request
            })
            results["treatment_recommendation"] = treatment_result
            results["workflow_steps"].append("Treatment recommendations generated with AI")
            
            # Step 3: Size RO system if needed
            if "Reverse Osmosis" in treatment_result.get("primary_treatment", ""):
                ro_tool = await builder.get_tool("ro_sizing")
                ro_result = await ro_tool({
                    "treatment_specs": analysis_result,
                    "flow_requirements": {"daily_flow_rate": customer_request.get("daily_flow_rate", 1000)}
                })
                results["ro_sizing"] = ro_result
                results["workflow_steps"].append("RO system sized with AI engineering analysis")
            
            # Step 4: Generate quotation
            quotation_tool = await builder.get_tool("quotation_generator")
            quotation_result = await quotation_tool({
                "system_specs": {**analysis_result, **treatment_result},
                "customer_budget": customer_request.get("budget", {})
            })
            results["quotation"] = quotation_result
            results["workflow_steps"].append("Quotation generated with AI cost analysis")
            
            # Final AI reasoning summary
            if config.enable_reasoning:
                ai_engine = AIReasoningEngine(config)
                final_reasoning = await ai_engine._call_nvidia_ai(
                    "You are summarizing a complete water treatment analysis workflow.",
                    f"Provide a final executive summary of this analysis: {json.dumps(results, indent=2)}"
                )
                results["executive_summary"] = final_reasoning.get("reasoning", "Analysis completed successfully")
            
            return results
            
        except Exception as e:
            return {
                "error": str(e),
                "workflow_steps": results.get("workflow_steps", []),
                "partial_results": results
            }
    
    yield FunctionInfo.from_fn(
        _orchestrate_workflow,
        description="Complete water treatment analysis workflow with AI reasoning at each step",
        input_model={"input_data": dict},
        output_model=dict
    )