# SPDX-FileCopyrightText: Copyright (c) 2024-2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ReasoningEngine:
    """
    Engine for generating reasoning explanations using LLM prompts.
    Loads prompts from prompts.py and provides methods to generate reasoning.
    """
    
    def __init__(self, llm_provider):
        """
        Initialize the reasoning engine with an LLM provider.
        
        Args:
            llm_provider: The LLM provider to use for generating reasoning
        """
        self.llm = llm_provider
        
        # Load prompts from prompts.py
        try:
            from prompts import (
                ANALYSIS_REASONING_PROMPT,
                TREATMENT_REASONING_PROMPT,
                RO_SIZING_REASONING_PROMPT,
                QUOTATION_REASONING_PROMPT
            )
            
            self.prompts = {
                "analysis": ANALYSIS_REASONING_PROMPT,
                "treatment": TREATMENT_REASONING_PROMPT,
                "ro_sizing": RO_SIZING_REASONING_PROMPT,
                "quotation": QUOTATION_REASONING_PROMPT
            }
            logger.info("Successfully loaded reasoning prompts from prompts.py")
        except ImportError as e:
            logger.error(f"Failed to import prompts from prompts.py: {e}")
            # Fallback prompts if import fails
            self.prompts = self._get_fallback_prompts()
            logger.info("Using fallback reasoning prompts")
        except AttributeError as e:
            logger.error(f"Missing prompt in prompts.py: {e}")
            # Fallback prompts if attributes are missing
            self.prompts = self._get_fallback_prompts()
            logger.info("Using fallback reasoning prompts")
    
    async def generate_reasoning(self, prompt_type: str, **kwargs) -> str:
        """
        Generate reasoning using the appropriate prompt.
        
        Args:
            prompt_type: Type of prompt to use (analysis, treatment, ro_sizing, quotation)
            **kwargs: Parameters to format the prompt with
            
        Returns:
            str: Generated reasoning text
            
        Raises:
            ValueError: If prompt_type is unknown
        """
        if prompt_type not in self.prompts:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        
        try:
            # Format prompt with provided kwargs
            formatted_prompt = self.prompts[prompt_type].format(**kwargs)
            
            # Generate reasoning using LLM
            response = await self.llm.agenerate(formatted_prompt)
            
            return response.text
        except KeyError as e:
            logger.error(f"Missing parameter for prompt formatting: {e}")
            return f"Error generating reasoning: missing parameter {e}"
        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            return f"Error generating reasoning: {e}"
    
    def _get_fallback_prompts(self) -> Dict[str, str]:
        """
        Get fallback prompts in case prompts.py is missing or incomplete.
        
        Returns:
            Dict[str, str]: Dictionary of fallback prompts
        """
        return {
            "analysis": """
            Analyze the following water parameters against guidelines:
            Parameters: {water_parameters}
            Guidelines: {guideline}
            Violations found: {parameter_violations}
            
            Explain why these parameters are concerning and their potential impact on water quality.
            """,
            
            "treatment": """
            Based on the following water parameter violations: {parameter_violations}
            And customer requirements:
            - Location: {location}
            - Water source: {water_source}
            - Usage: {water_usage}
            - Flow rate: {daily_flow_rate}
            - Budget: {budget}
            
            I've recommended these treatment systems: {recommended_systems}
            
            Provide a detailed explanation of:
            1. Why each system component is necessary based on the specific parameter violations
            2. How these components work together to address all water quality issues
            3. Why this approach prioritizes water cleaning effectiveness while considering the customer's budget
            4. Any trade-offs made and their justification
            """,
            
            "ro_sizing": """
            Based on:
            - Customer's daily flow rate: {daily_flow_rate}
            - Water usage: {water_usage}
            - Recommended RO system: {ro_components}
            
            I've calculated the following sizing specifications:
            {sizing_results}
            
            Provide a detailed explanation of:
            1. How these dimensions were calculated and why they're appropriate
            2. How the system capacity matches the customer's needs
            3. Any safety factors included and why
            4. How this sizing optimizes for both performance and cost-effectiveness
            5. Any potential future scalability considerations
            """,
            
            "quotation": """
            Based on the recommended water treatment system:
            - Components: {ro_components}
            - Sizing: {sizing_specifications}
            - Pretreatment: {pretreatment_plan}
            
            I've calculated the following costs:
            - Component costs: {component_costs}
            - Installation costs: {installation_costs}
            - First-year maintenance costs: {maintenance_costs}
            - Total cost: {total_cost} {currency}
            
            Customer's budget: {budget_amount} {currency}
            Within budget: {within_budget}
            
            Provide a detailed explanation of:
            1. How each cost was calculated and what it includes
            2. The value proposition for the customer (ROI, water quality benefits, etc.)
            3. If not within budget, what compromises could be made and their impacts
            4. Long-term cost considerations (operational costs, component lifespan, etc.)
            5. Why this represents the best solution for the customer's specific needs
            """
        }


def compile_comprehensive_reasoning(reasoning_list: list) -> str:
    """
    Compile multiple reasoning outputs into a comprehensive report.
    
    Args:
        reasoning_list: List of reasoning outputs from different tools
        
    Returns:
        str: Comprehensive reasoning report
    """
    if not reasoning_list or all(not r for r in reasoning_list):
        return "No reasoning provided by any tool."
    
    sections = [
        "# Water Treatment System Comprehensive Analysis",
        "",
        "## Water Quality Analysis",
        reasoning_list[0] if len(reasoning_list) > 0 and reasoning_list[0] else "No analysis reasoning provided.",
        "",
        "## Treatment Recommendation Rationale",
        reasoning_list[1] if len(reasoning_list) > 1 and reasoning_list[1] else "No treatment reasoning provided.",
        "",
        "## System Sizing Justification",
        reasoning_list[2] if len(reasoning_list) > 2 and reasoning_list[2] else "No sizing reasoning provided.",
        "",
        "## Cost and Value Analysis",
        reasoning_list[3] if len(reasoning_list) > 3 and reasoning_list[3] else "No quotation reasoning provided.",
        "",
        "## Conclusion",
        "This comprehensive analysis provides a complete picture of the water treatment solution, "
        "from initial water quality assessment through treatment selection, system sizing, and cost analysis. "
        "Each component of the solution has been carefully selected and sized to address the specific water quality "
        "issues while considering the customer's requirements and budget constraints."
    ]
    
    return "\n".join(sections)
