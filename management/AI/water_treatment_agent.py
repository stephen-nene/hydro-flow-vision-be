# water_treatment_agent.py - Main orchestration with NVIDIA AI integration

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from pydantic import BaseModel, Field

# Import our custom components
from register_water import (
    WaterAnalysisConfig, 
    CustomerRequestInput,
    TreatmentSpecs,
    TreatmentRecommendation,
    ROSizingOutput,
    QuotationOutput,
    AIReasoningEngine
)

from prompts import (
    LAB_ANALYSIS_SYSTEM_MESSAGE,
    TREATMENT_RECOMMENDATION_SYSTEM_MESSAGE,
    RO_SIZING_SYSTEM_MESSAGE,
    QUOTATION_SYSTEM_MESSAGE,
    MAIN_AGENT_SYSTEM_MESSAGE,
    build_analysis_prompt,
    build_treatment_prompt,
    build_ro_sizing_prompt,
    build_quotation_prompt,
    EXECUTIVE_SUMMARY_TEMPLATE,
    QA_CONSISTENCY_CHECK,
    format_for_nvidia_ai
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WaterTreatmentWorkflowConfig(BaseModel):
    """Configuration for the complete water treatment workflow"""
    
    # AI Model Configuration
    ai_model: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    enable_ai_reasoning: bool = True
    reasoning_temperature: float = 0.7
    max_reasoning_tokens: int = 2048
    
    # Workflow Configuration
    enable_quality_assurance: bool = True
    enable_cost_optimization: bool = True
    enable_risk_assessment: bool = True
    
    # Data Sources
    guideline_database_url: str = "https://water-standards-db.com/api"
    component_database_url: str = "https://treatment-components-db.com/api"
    cost_database_url: str = "https://water-treatment-costs.com/api"
    
    # Validation Settings
    min_confidence_threshold: float = 0.7
    require_regulatory_check: bool = True
    enable_sustainability_assessment: bool = True

class WorkflowExecutionResult(BaseModel):
    """Complete workflow execution result"""
    
    workflow_id: str
    execution_timestamp: datetime
    input_data: Dict[str, Any]
    
    # Stage Results
    analysis_result: Optional[Dict[str, Any]] = None
    treatment_result: Optional[Dict[str, Any]] = None
    sizing_result: Optional[Dict[str, Any]] = None
    quotation_result: Optional[Dict[str, Any]] = None
    
    # Quality Assurance
    qa_checks: List[Dict[str, Any]] = []
    confidence_scores: Dict[str, float] = {}
    risk_assessment: Dict[str, Any] = {}
    
    # Executive Summary
    executive_summary: str = ""
    recommendations: List[str] = []
    next_steps: List[str] = []
    
    # Status
    execution_status: str = "completed"
    errors: List[str] = []
    warnings: List[str] = []

class WaterTreatmentOrchestrator:
    """Main orchestrator for the water treatment workflow"""
    
    def __init__(self, config: WaterTreatmentWorkflowConfig):
        self.config = config
        self.ai_engine = AIReasoningEngine(WaterAnalysisConfig(
            ai_model=config.ai_model,
            enable_reasoning=config.enable_ai_reasoning,
            reasoning_temperature=config.reasoning_temperature,
            max_reasoning_tokens=config.max_reasoning_tokens
        ))
        
    async def execute_workflow(self, input_data: Dict[str, Any], builder: Builder) -> WorkflowExecutionResult:
        """Execute the complete water treatment analysis workflow"""
        
        workflow_id = f"wt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = WorkflowExecutionResult(
            workflow_id=workflow_id,
            execution_timestamp=datetime.now(),
            input_data=input_data
        )
        
        logger.info(f"Starting workflow execution: {workflow_id}")
        
        try:
            # Step 1: Lab Report Analysis
            logger.info("Executing lab report analysis...")
            analysis_result = await self._execute_lab_analysis(input_data, builder)
            result.analysis_result = analysis_result
            result.confidence_scores["analysis"] = analysis_result.get("confidence_score", 0.0)
            
            # Step 2: Treatment Recommendation
            logger.info("Generating treatment recommendations...")
            treatment_result = await self._execute_treatment_recommendation(
                analysis_result, input_data, builder
            )
            result.treatment_result = treatment_result
            result.confidence_scores["treatment"] = treatment_result.get("confidence_score", 0.0)
            
            # Step 3: RO Sizing (if applicable)
            if self._requires_ro_sizing(treatment_result):
                logger.info("Sizing RO system...")
                sizing_result = await self._execute_ro_sizing(
                    analysis_result, input_data, builder
                )
                result.sizing_result = sizing_result
                result.confidence_scores["sizing"] = sizing_result.get("confidence_score", 0.0)
            
            # Step 4: Quotation Generation
            logger.info("Generating quotation...")
            quotation_result = await self._execute_quotation_generation(
                analysis_result, treatment_result, result.sizing_result, input_data, builder
            )
            result.quotation_result = quotation_result
            result.confidence_scores["quotation"] = quotation_result.get("confidence_score", 0.0)
            
            # Step 5: Quality Assurance
            if self.config.enable_quality_assurance:
                logger.info("Performing quality assurance checks...")
                qa_results = await self._perform_quality_assurance(result)
                result.qa_checks = qa_results
            
            # Step 6: Risk Assessment
            if self.config.enable_risk_assessment:
                logger.info("Conducting risk assessment...")
                risk_assessment = await self._conduct_risk_assessment(result)
                result.risk_assessment = risk_assessment
            
            # Step 7: Executive Summary Generation
            logger.info("Generating executive summary...")
            executive_summary = await self._generate_executive_summary(result)
            result.executive_summary = executive_summary
            
            # Final validation
            await self._validate_workflow_results(result)
            
            logger.info(f"Workflow execution completed successfully: {workflow_id}")
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            result.execution_status = "failed"
            result.errors.append(str(e))
        
        return result
    
    async def _execute_lab_analysis(self, input_data: Dict[str, Any], builder: Builder) -> Dict[str, Any]:
        """Execute lab report analysis with AI reasoning"""
        
        customer_request = input_data.get("customer_request", {})
        guidelines = input_data.get("guidelines", [])
        
        # Get the analysis tool
        analysis_tool = await builder.get_tool("analyse_lab_report")
        
        # Execute analysis
        analysis_result = await analysis_tool({
            "customer_request": customer_request,
            "guideline": guidelines
        })
        
        # Add AI reasoning if enabled
        if self.config.enable_ai_reasoning:
            analysis_prompt = build_analysis_prompt(customer_request, guidelines)
            ai_reasoning = await self.ai_engine._call_nvidia_ai(
                LAB_ANALYSIS_SYSTEM_MESSAGE,
                analysis_prompt
            )
            analysis_result["ai_reasoning"] = ai_reasoning.get("reasoning", "")
            analysis_result["confidence_score"] = ai_reasoning.get("confidence", 0.8)
        
        return analysis_result
    
    async def _execute_treatment_recommendation(
        self, analysis_result: Dict[str, Any], input_data: Dict[str, Any], builder: Builder
    ) -> Dict[str, Any]:
        """Execute treatment recommendation with AI reasoning"""
        
        customer_request = input_data.get("customer_request", {})
        
        # Get the treatment tool
        treatment_tool = await builder.get_tool("treatment_recommendation")
        
        # Execute treatment recommendation
        treatment_result = await treatment_tool({
            "treatment_specs": analysis_result,
            "customer_context": customer_request
        })
        
        # Add AI reasoning if enabled
        if self.config.enable_ai_reasoning:
            treatment_prompt = build_treatment_prompt(analysis_result, customer_request)
            ai_reasoning = await self.ai_engine._call_nvidia_ai(
                TREATMENT_RECOMMENDATION_SYSTEM_MESSAGE,
                treatment_prompt
            )
            treatment_result["ai_reasoning"] = ai_reasoning.get("reasoning", "")
            treatment_result["confidence_score"] = ai_reasoning.get("confidence", 0.8)
        
        return treatment_result
    
    async def _execute_ro_sizing(
        self, analysis_result: Dict[str, Any], input_data: Dict[str, Any], builder: Builder
    ) -> Dict[str, Any]:
        """Execute RO sizing with AI reasoning"""
        
        customer_request = input_data.get("customer_request", {})
        flow_requirements = {
            "daily_flow_rate": customer_request.get("daily_flow_rate", 1000),
            "peak_factor": 1.5,
            "operating_hours": 16
        }
        
        # Get the RO sizing tool
        ro_tool = await builder.get_tool("ro_sizing")
        
        # Execute RO sizing
        sizing_result = await ro_tool({
            "treatment_specs": analysis_result,
            "flow_requirements": flow_requirements
        })
        
        # Add AI reasoning if enabled
        if self.config.enable_ai_reasoning:
            sizing_prompt = build_ro_sizing_prompt(analysis_result, flow_requirements)
            ai_reasoning = await self.ai_engine._call_nvidia_ai(
                RO_SIZING_SYSTEM_MESSAGE,
                sizing_prompt
            )
            sizing_result["ai_reasoning"] = ai_reasoning.get("reasoning", "")
            sizing_result["confidence_score"] = ai_reasoning.get("confidence", 0.8)
        
        return sizing_result
    
    async def _execute_quotation_generation(
        self, analysis_result: Dict[str, Any], treatment_result: Dict[str, Any],
        sizing_result: Optional[Dict[str, Any]], input_data: Dict[str, Any], builder: Builder
    ) -> Dict[str, Any]:
        """Execute quotation generation with AI reasoning"""
        
        customer_request = input_data.get("customer_request", {})
        customer_budget = customer_request.get("budget", {})
        
        # Combine system specifications
        system_specs = {
            **analysis_result,
            **treatment_result
        }
        if sizing_result:
            system_specs.update(sizing_result)
        
        # Get the quotation tool
        quotation_tool = await builder.get_tool("quotation_generator")
        
        # Execute quotation generation
        quotation_result = await quotation_tool({
            "system_specs": system_specs,
            "customer_budget": customer_budget
        })
        
        # Add AI reasoning if enabled
        if self.config.enable_ai_reasoning:
            quotation_prompt = build_quotation_prompt(system_specs, customer_budget)
            ai_reasoning = await self.ai_engine._call_nvidia_ai(
                QUOTATION_SYSTEM_MESSAGE,
                quotation_prompt
            )
            quotation_result["ai_reasoning"] = ai_reasoning.get("reasoning", "")
            quotation_result["confidence_score"] = ai_reasoning.get("confidence", 0.8)
        
        return quotation_result
    
    def _requires_ro_sizing(self, treatment_result: Dict[str, Any]) -> bool:
        """Determine if RO sizing is required based on treatment recommendations"""
        
        primary_treatment = treatment_result.get("primary_treatment", "")
        secondary_treatments = treatment_result.get("secondary_treatments", [])
        
        ro_indicators = ["reverse osmosis", "ro", "membrane", "desalination"]
        
        return (
            any(indicator in primary_treatment.lower() for indicator in ro_indicators) or
            any(any(indicator in treatment.lower() for indicator in ro_indicators) 
                for treatment in secondary_treatments)
        )
    
    async def _perform_quality_assurance(self, result: WorkflowExecutionResult) -> List[Dict[str, Any]]:
        """Perform quality assurance checks on workflow results"""
        
        qa_checks = []
        
        # Consistency check
        consistency_issues = await self._check_consistency(result)
        if consistency_issues:
            qa_checks.append({
                "check_type": "consistency",
                "status": "warning",
                "issues": consistency_issues
            })
        
        # Completeness check
        completeness_issues = await self._check_completeness(result)
        if completeness_issues:
            qa_checks.append({
                "check_type": "completeness", 
                "status": "warning",
                "issues": completeness_issues
            })
        
        # Confidence threshold check
        low_confidence_stages = [
            stage for stage, score in result.confidence_scores.items()
            if score < self.config.min_confidence_threshold
        ]
        if low_confidence_stages:
            qa_checks.append({
                "check_type": "confidence",
                "status": "warning",
                "low_confidence_stages": low_confidence_stages
            })
        
        return qa_checks
    
    async def _check_consistency(self, result: WorkflowExecutionResult) -> List[str]:
        """Check consistency across workflow stages"""
        
        issues = []
        
        # Check if treatments address all identified violations
        if result.analysis_result and result.treatment_result:
            violations = result.analysis_result.get("required_treatments", [])
            treatments = result.treatment_result.get("secondary_treatments", [])
            
            unaddressed_violations = set(violations) - set(treatments)
            if unaddressed_violations:
                issues.append(f"Unaddressed violations: {list(unaddressed_violations)}")
        
        # Check if sizing matches treatment requirements
        if result.treatment_result and result.sizing_result:
            treatment_capacity = result.treatment_result.get("system_capacity")
            sizing_capacity = result.sizing_result.get("system_capacity")
            
            if treatment_capacity and sizing_capacity:
                if abs(treatment_capacity - sizing_capacity) > treatment_capacity * 0.2:
                    issues.append("Capacity mismatch between treatment and sizing stages")
        
        return issues
    
    async def _check_completeness(self, result: WorkflowExecutionResult) -> List[str]:
        """Check completeness of workflow results"""
        
        issues = []
        
        # Check if all required stages completed
        required_stages = ["analysis_result", "treatment_result", "quotation_result"]
        for stage in required_stages:
            if not getattr(result, stage):
                issues.append(f"Missing {stage}")
        
        # Check if critical information is present
        if result.quotation_result:
            if not result.quotation_result.get("total_cost"):
                issues.append("Missing total cost in quotation")
            if not result.quotation_result.get("cost_breakdown"):
                issues.append("Missing cost breakdown in quotation")
        
        return issues
    
    async def _conduct_risk_assessment(self, result: WorkflowExecutionResult) -> Dict[str, Any]:
        """Conduct risk assessment for the recommended solution"""
        
        risk_assessment = {
            "technical_risks": [],
            "financial_risks": [],
            "operational_risks": [],
            "regulatory_risks": [],
            "overall_risk_level": "medium"
        }
        
        # Technical risks
        if result.confidence_scores:
            avg_confidence = sum(result.confidence_scores.values()) / len(result.confidence_scores)
            if avg_confidence < 0.7:
                risk_assessment["technical_risks"].append("Low confidence in technical recommendations")
        
        # Financial risks
        if result.quotation_result:
            total_cost = result.quotation_result.get("total_cost", 0)
            customer_budget = result.input_data.get("customer_request", {}).get("budget", {})
            if isinstance(customer_budget, dict) and customer_budget.get("total_budget"):
                if total_cost > customer_budget["total_budget"] * 1.2:
                    risk_assessment["financial_risks"].append("Recommended solution exceeds budget by >20%")
        
        # Operational risks
        if result.treatment_result:
            treatment_complexity = len(result.treatment_result.get("secondary_treatments", []))
            if treatment_complexity > 3:
                risk_assessment["operational_risks"].append("High system complexity may require skilled operators")
        
        return risk_assessment
    
    async def _generate_executive_summary(self, result: WorkflowExecutionResult) -> str:
        """Generate executive summary using AI"""
        
        if not self.config.enable_ai_reasoning:
            return "Workflow completed successfully. Detailed results available in individual stages."
        
        summary_data = {
            "analysis_summary": result.analysis_result.get("ai_reasoning", "Analysis completed"),
            "treatment_summary": result.treatment_result.get("ai_reasoning", "Treatment designed"),
            "cost_summary": result.quotation_result.get("ai_reasoning", "Quotation generated"),
            "confidence_scores": result.confidence_scores,
            "qa_issues": len(result.qa_checks),
            "risk_level": result.risk_assessment.get("overall_risk_level", "medium")
        }
        
        summary_prompt = f"""
Generate an executive summary for a water treatment system analysis.

Workflow Results Summary:
{json.dumps(summary_data, indent=2)}

Please provide a concise executive summary that covers:
1. Overall water quality assessment
2. Recommended solution overview
3. Investment requirements and ROI
4. Key risks and mitigation strategies
5. Implementation timeline and next steps

Format the summary for business decision-makers who need clear, actionable information.
"""
        
        ai_response = await self.ai_engine._call_nvidia_ai(
            MAIN_AGENT_SYSTEM_MESSAGE,
            summary_prompt
        )
        
        return ai_response.get("reasoning", "Executive summary generation failed")
    
    async def _validate_workflow_results(self, result: WorkflowExecutionResult):
        """Final validation of workflow results"""
        
        # Check for critical errors
        if not result.analysis_result:
            result.errors.append("Lab analysis failed to complete")
            result.execution_status = "failed"
        
        if not result.treatment_result:
            result.errors.append("Treatment recommendation failed to complete")
            result.execution_status = "failed"
        
        if not result.quotation_result:
            result.errors.append("Quotation generation failed to complete")
            result.execution_status = "failed"
        
        # Check confidence levels
        low_confidence_count = sum(
            1 for score in result.confidence_scores.values()
            if score < self.config.min_confidence_threshold
        )
        
        if low_confidence_count > 2:
            result.warnings.append("Multiple stages have low confidence scores")
        
        # Set final status
        if result.errors:
            result.execution_status = "failed"
        elif result.warnings or result.qa_checks:
            result.execution_status = "completed_with_warnings"
        else:
            result.execution_status = "completed"

# Main registration function
@register_function()
async def water_treatment_agent(builder: Builder):
    """Main water treatment agent with full AI integration"""
    
    config = WaterTreatmentWorkflowConfig()
    orchestrator = WaterTreatmentOrchestrator(config)
    
    async def run_complete_analysis(input_data: dict) -> dict:
        """Execute the complete water treatment analysis workflow"""
        
        try:
            # Execute the workflow
            result = await orchestrator.execute_workflow(input_data, builder)
            
            # Return structured result
            return {
                "workflow_id": result.workflow_id,
                "execution_status": result.execution_status,
                "analysis": result.analysis_result,
                "treatment_recommendation": result.treatment_result,
                "ro_sizing": result.sizing_result,
                "quotation": result.quotation_result,
                "executive_summary": result.executive_summary,
                "quality_assurance": result.qa_checks,
                "risk_assessment": result.risk_assessment,
                "confidence_scores": result.confidence_scores,
                "errors": result.errors,
                "warnings": result.warnings
            }
            
        except Exception as e:
            logger.error(f"Water treatment agent execution failed: {str(e)}")
            return {
                "execution_status": "failed",
                "error": str(e),
                "workflow_id": f"failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
    
    yield FunctionInfo.from_fn(
        run_complete_analysis,
        description="Complete water treatment analysis system with AI reasoning, quality assurance, and risk assessment",
        input_model={"input_data": dict},
        output_model=dict
    )