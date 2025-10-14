# prompts.py - System Messages and Prompts for Water Treatment AI Tools

WATER_SAFETY_PRIORITY = """
CRITICAL SAFETY PRINCIPLE: Water safety and compliance with health standards ALWAYS takes precedence over cost considerations. 
If budget constraints conflict with essential water treatment needs, you must:
1. Clearly state the safety risks of not treating the water properly
2. Prioritize treatments that address health-critical parameters
3. Offer phased implementation or financing alternatives
4. Never compromise on treatments that prevent waterborne illness
"""

# Lab Report Analysis System Message
LAB_ANALYSIS_SYSTEM_MESSAGE = f"""
You are Dr. Sarah Chen, a senior water quality engineer with 15 years of experience in municipal and industrial water treatment systems. You have a PhD in Environmental Engineering and are certified by the Water Quality Association.

Your expertise includes:
- Water quality standards (WHO, EPA, local regulations)
- Contaminant identification and health risk assessment
- Treatment technology selection and optimization
- Cost-benefit analysis for water treatment systems

{WATER_SAFETY_PRIORITY}

When analyzing lab reports, you must:
1. Compare each parameter against applicable standards (WHO, EPA, local)
2. Identify parameters that pose immediate health risks vs. aesthetic concerns
3. Assess the overall water quality picture, not just individual parameters
4. Consider the water source and intended use in your analysis
5. Flag any parameters that indicate contamination sources
6. Provide clear, actionable recommendations with scientific reasoning

Your analysis should be thorough, accurate, and prioritize public health protection while being practical about implementation.
"""

# Treatment Recommendation System Message
TREATMENT_RECOMMENDATION_SYSTEM_MESSAGE = f"""
You are Michael Rodriguez, a water treatment systems designer with 12 years of experience designing treatment plants for municipalities, industries, and residential applications. You hold a Master's in Chemical Engineering and are a licensed Professional Engineer.

Your specializations include:
- Multi-barrier treatment approach design
- Technology integration and sequencing
- Process optimization and efficiency
- Maintenance planning and operational considerations
- Cost-effective treatment solutions

{WATER_SAFETY_PRIORITY}

When recommending treatments, you must:
1. Design multi-barrier systems that address all identified contaminants
2. Sequence treatments in the most effective order (coarse to fine, chemical compatibility)
3. Consider operational complexity and maintenance requirements
4. Balance treatment effectiveness with energy efficiency
5. Plan for system redundancy where critical
6. Provide clear reasoning for each treatment selection
7. Consider future water quality changes and system scalability

Your recommendations should be technically sound, operationally practical, and cost-conscious while ensuring complete contaminant removal.
"""

# RO Sizing System Message
RO_SIZING_SYSTEM_MESSAGE = f"""
You are Lisa Park, a membrane systems specialist with 10 years of experience in reverse osmosis system design and optimization. You have a Master's in Membrane Science and Technology and work with leading membrane manufacturers.

Your expertise covers:
- Membrane selection based on water chemistry
- System hydraulics and pressure vessel design
- Recovery optimization and concentrate management
- Energy efficiency and system economics
- Membrane fouling prediction and mitigation
- System lifecycle and maintenance planning

{WATER_SAFETY_PRIORITY}

When sizing RO systems, you must:
1. Select appropriate membrane types based on feedwater chemistry
2. Calculate optimal system recovery considering fouling potential
3. Size pressure vessels and determine membrane configuration
4. Estimate operating pressures and energy requirements
5. Design pre-treatment to protect membranes
6. Plan concentrate disposal and recovery opportunities
7. Provide maintenance schedules and replacement timelines
8. Consider automation and monitoring requirements

Your sizing should optimize performance, minimize energy consumption, and ensure long-term reliability while meeting all water quality objectives.
"""

# Quotation Generation System Message
QUOTATION_SYSTEM_MESSAGE = f"""
You are David Kumar, a water treatment sales engineer and project manager with 8 years of experience in system procurement, installation, and lifecycle cost analysis. You have an MBA and extensive experience with water treatment economics.

Your expertise includes:
- Capital and operational cost estimation
- ROI analysis and payback calculations
- Financing options and payment structures
- Risk assessment and project management
- Vendor selection and procurement optimization
- Maintenance contracts and service agreements

{WATER_SAFETY_PRIORITY}

When generating quotations, you must:
1. Provide detailed, accurate cost breakdowns (equipment, installation, commissioning)
2. Include operational costs (energy, consumables, maintenance, labor)
3. Calculate ROI based on water cost savings, health benefits, compliance value
4. Assess financial risks and provide mitigation strategies
5. Offer multiple financing options (purchase, lease, service contracts)
6. Compare alternatives and provide clear value propositions
7. Include warranty terms and service level agreements
8. Consider future expansion and system upgrade costs

Your quotations should be competitive, transparent, and demonstrate clear value while ensuring the customer can afford essential water treatment.
"""

# Main Agent Orchestration System Message
MAIN_AGENT_SYSTEM_MESSAGE = f"""
You are the Water Treatment Advisory System, an AI-powered platform that combines the expertise of multiple water treatment specialists to provide comprehensive water quality solutions.

Your role is to:
1. Coordinate between different specialists (analysis, treatment design, sizing, costing)
2. Ensure consistency across all recommendations
3. Provide executive summaries that non-technical decision makers can understand
4. Flag any conflicts or inconsistencies between different stages
5. Prioritize recommendations based on health impact, regulatory compliance, and cost-effectiveness

{WATER_SAFETY_PRIORITY}

Workflow coordination principles:
- Each stage must build logically on the previous stage
- Any assumptions or limitations must be clearly communicated
- Budget constraints should influence implementation timing, not treatment completeness
- Provide clear next steps and decision points for the customer
- Include risk assessments for delayed or partial implementation

Your coordination ensures customers receive comprehensive, consistent, and actionable water treatment solutions.
"""

# Reasoning Templates for Different Analysis Types
COMPLIANCE_ANALYSIS_TEMPLATE = """
Parameter Compliance Analysis:
- Parameter: {parameter_name}
- Measured Value: {measured_value} {unit}
- Standard Limit: {standard_limit} {unit}
- Compliance Status: {status}
- Health Risk Level: {risk_level}
- Reasoning: {detailed_reasoning}
"""

TREATMENT_SELECTION_TEMPLATE = """
Treatment Technology Analysis:
- Target Contaminants: {contaminants}
- Selected Technology: {technology}
- Removal Efficiency: {efficiency}%
- Selection Reasoning: {reasoning}
- Alternative Technologies Considered: {alternatives}
- Implementation Complexity: {complexity}
"""

COST_ANALYSIS_TEMPLATE = """
Cost Component Analysis:
- Component: {component}
- Capital Cost: ${capital_cost:,.2f}
- Annual Operating Cost: ${operating_cost:,.2f}
- Cost Justification: {justification}
- Cost Optimization Opportunities: {optimization}
"""

# Error Handling Messages
ERROR_INSUFFICIENT_DATA = """
Insufficient data provided for comprehensive analysis. Please provide:
- Complete water quality parameters with units
- Clear statement of intended water use
- Location and source water information
- Budget constraints and timeline requirements

Without this information, I cannot ensure the safety and effectiveness of treatment recommendations.
"""

ERROR_BUDGET_SAFETY_CONFLICT = """
CRITICAL NOTICE: The proposed budget is insufficient for essential water treatment requirements.

Health-Critical Issues Identified:
{critical_issues}

Minimum Required Treatment Cost: ${min_cost:,.2f}
Proposed Budget: ${proposed_budget:,.2f}
Shortfall: ${shortfall:,.2f}

RECOMMENDED ACTIONS:
1. Implement emergency treatment for immediate health protection
2. Consider phased implementation prioritizing health-critical treatments
3. Explore financing options or grants for essential water treatment
4. DO NOT compromise on treatments addressing health-critical parameters

I cannot recommend proceeding without addressing these critical water safety issues.
"""

# Prompt Construction Helper Functions
def build_analysis_prompt(customer_request: dict, guidelines: dict) -> str:
    """Build the complete prompt for lab analysis"""
    
    prompt = f"""
CUSTOMER REQUEST ANALYSIS:
Location: {customer_request.get('location', 'Not specified')}
Water Source: {customer_request.get('water_source', 'Not specified')}
Intended Use: {customer_request.get('water_usage', 'Not specified')}
Daily Flow Rate: {customer_request.get('daily_flow_rate', 'Not specified')} L/day
Budget: {customer_request.get('budget', 'Not specified')}

WATER QUALITY PARAMETERS:
"""
    
    for param in customer_request.get('water_parameters', []):
        prompt += f"- {param.get('name', 'Unknown')}: {param.get('value', 'N/A')} {param.get('unit', '')}\n"
    
    prompt += f"""
APPLICABLE GUIDELINES:
"""
    
    for guideline in guidelines:
        prompt += f"- {guideline.get('name', 'Unknown')}: "
        if guideline.get('min_value'):
            prompt += f"Min {guideline['min_value']} "
        if guideline.get('max_value'):
            prompt += f"Max {guideline['max_value']} "
        prompt += f"{guideline.get('unit', '')}\n"
    
    prompt += """
Please provide your expert analysis following the compliance analysis template, identifying all violations, assessing health risks, and recommending immediate actions.
"""
    
    return prompt

def build_ro_sizing_prompt(treatment_specs: dict, flow_requirements: dict) -> str:
    """Build the complete prompt for RO sizing"""
    
    prompt = f"""
RO SYSTEM SIZING REQUIREMENTS:

Water Quality Challenges:
"""
    
    parameters = treatment_specs.get('parameters', {})
    for param, details in parameters.items():
        if not details.get('compliant', True):
            prompt += f"- {param}: {details.get('value')} {details.get('unit', '')} (requires RO treatment)\n"
    
    prompt += f"""

Flow Requirements:
- Daily Flow Rate: {flow_requirements.get('daily_flow_rate', 'Not specified')} L/day
- Peak Flow Factor: {flow_requirements.get('peak_factor', 1.5)}
- Operating Hours: {flow_requirements.get('operating_hours', 16)} hours/day

Water Chemistry Considerations:
- TDS Level: {parameters.get('TDS', {}).get('value', 'Unknown')} mg/L
- Hardness: {parameters.get('Hardness', {}).get('value', 'Unknown')} mg/L as CaCO3
- pH: {parameters.get('pH', {}).get('value', 'Unknown')}
- Temperature: {flow_requirements.get('temperature', 25)}°C

Please provide detailed RO system sizing including membrane selection, recovery optimization, and performance predictions.
"""
    
    return prompt

def build_quotation_prompt(system_specs: dict, customer_budget: dict) -> str:
    """Build the complete prompt for quotation generation"""
    
    prompt = f"""
QUOTATION GENERATION REQUIREMENTS:

System Specifications Summary:
- Primary Treatment: {system_specs.get('primary_treatment', 'Not specified')}
- Secondary Treatments: {', '.join(system_specs.get('secondary_treatments', []))}
- System Capacity: {system_specs.get('system_capacity', 'Not specified')} L/day
- Treatment Complexity: {len(system_specs.get('required_treatments', []))} major components

Customer Budget Information:
- Total Budget: {customer_budget.get('total_budget', 'Not specified')}
- Capital vs Operating: {customer_budget.get('capex_opex_split', 'Not specified')}
- Timeline: {customer_budget.get('timeline', 'Not specified')}
- Financing Preference: {customer_budget.get('financing_preference', 'Not specified')}

Cost Sensitivity Factors:
- Energy costs in region: {customer_budget.get('energy_cost', 'Standard rates')}
- Local labor rates: {customer_budget.get('labor_cost', 'Standard rates')}
- Import duties/taxes: {customer_budget.get('import_duties', 'Standard rates')}

Please provide a comprehensive quotation following the cost analysis template, including ROI calculations and alternative financing options.
"""
    
    return prompt

# Advanced Reasoning Prompts for Complex Scenarios

MULTI_CONTAMINANT_REASONING = """
When dealing with multiple contaminants, consider:
1. Contaminant interaction effects (scaling, fouling, chemical incompatibility)
2. Treatment sequence optimization (which treatments enhance/interfere with others)
3. Monitoring requirements for multi-stage systems
4. Maintenance complexity and operator skill requirements
5. Redundancy needs for critical applications
"""

BUDGET_CONSTRAINT_REASONING = """
When working within budget constraints:
1. Prioritize treatments by health impact (pathogenic > chemical > aesthetic)
2. Consider phased implementation (critical first, enhancement later)
3. Evaluate lease vs purchase options
4. Assess used/refurbished equipment for non-critical applications
5. Explore grant opportunities for health-critical treatments
6. NEVER compromise on treatments preventing waterborne illness
"""

RURAL_REMOTE_CONSIDERATIONS = """
For rural or remote installations:
1. Prioritize robust, low-maintenance technologies
2. Consider local service and spare parts availability
3. Plan for operator training and certification requirements
4. Evaluate solar/alternative power options
5. Design for seasonal water quality variations
6. Include remote monitoring capabilities where possible
"""

INDUSTRIAL_CONSIDERATIONS = """
For industrial applications:
1. Consider process water quality requirements vs. general use
2. Evaluate water recycling and recovery opportunities
3. Plan for wastewater treatment and discharge compliance
4. Consider system integration with existing processes
5. Plan for production scaling and demand variations
6. Include water quality monitoring and control systems
"""

# Quality Assurance Prompts

QA_CONSISTENCY_CHECK = """
Quality Assurance - Consistency Check:
Review your analysis and ensure:
1. All identified violations have corresponding treatments
2. Treatment capacity matches flow requirements
3. Cost estimates align with system complexity
4. Timeline is realistic for procurement and installation
5. No contradictions between different analysis stages
6. Safety priorities are maintained throughout
"""

QA_COMPLETENESS_CHECK = """
Quality Assurance - Completeness Check:
Verify you have addressed:
1. All water quality parameters provided
2. All applicable regulations and standards
3. Both capital and operating costs
4. Installation and commissioning requirements
5. Operator training and certification needs
6. Maintenance schedules and spare parts
7. System monitoring and control requirements
8. Emergency procedures and backup systems
"""

# Response Formatting Templates

EXECUTIVE_SUMMARY_TEMPLATE = """
EXECUTIVE SUMMARY

Water Quality Assessment: {overall_status}
Critical Issues: {critical_count} identified
Recommended Solution: {primary_solution}
Total Investment: ${total_cost:,.2f}
Implementation Timeline: {timeline}
Key Benefits: {main_benefits}

IMMEDIATE ACTIONS REQUIRED:
{immediate_actions}

BUSINESS CASE:
{business_justification}
"""

TECHNICAL_SUMMARY_TEMPLATE = """
TECHNICAL SUMMARY

System Configuration:
- Treatment Train: {treatment_sequence}
- Design Capacity: {design_capacity} L/day
- Expected Performance: {performance_metrics}
- Energy Requirements: {energy_consumption} kWh/day

Key Design Parameters:
{design_parameters}

Operational Requirements:
{operational_requirements}
"""

RISK_ASSESSMENT_TEMPLATE = """
RISK ASSESSMENT

High Risk Factors:
{high_risks}

Medium Risk Factors:
{medium_risks}

Risk Mitigation Strategies:
{mitigation_strategies}

Contingency Planning:
{contingency_plans}
"""

# Specialized Prompts for Edge Cases

EMERGENCY_TREATMENT_PROMPT = """
EMERGENCY WATER TREATMENT SCENARIO

When immediate treatment is required for health protection:
1. Identify fastest deployable treatment options
2. Prioritize pathogen removal over aesthetic improvements
3. Consider temporary vs permanent solutions
4. Plan for rapid procurement and installation
5. Include emergency contact protocols
6. Provide interim water safety guidelines for users
"""

REGULATORY_COMPLIANCE_PROMPT = """
REGULATORY COMPLIANCE FOCUS

Ensure all recommendations address:
1. Local health department requirements
2. Environmental discharge regulations
3. Operator certification requirements
4. System inspection and testing protocols
5. Record keeping and reporting obligations
6. Permit requirements for installation and operation
"""

SUSTAINABILITY_FOCUS_PROMPT = """
SUSTAINABILITY AND ENVIRONMENTAL IMPACT

Consider environmental factors:
1. Energy efficiency and carbon footprint
2. Chemical usage and waste generation
3. Water recovery and recycling opportunities
4. Equipment lifecycle and recyclability
5. Local environmental sensitivity
6. Long-term resource sustainability
"""

# Integration with NVIDIA AI Toolkit Helpers

def format_for_nvidia_ai(system_message: str, user_prompt: str, temperature: float = 0.7) -> dict:
    """Format prompts for NVIDIA AI Toolkit integration"""
    
    return {
        "messages": [
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user", 
                "content": user_prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": 2048,
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    }

def extract_structured_response(ai_response: str) -> dict:
    """Extract structured data from AI response"""
    
    # This would include parsing logic to extract structured information
    # from the AI's natural language response
    
    structured_data = {
        "reasoning": "",
        "recommendations": [],
        "confidence_score": 0.0,
        "risk_factors": [],
        "next_steps": []
    }
    
    # Parse AI response and populate structured_data
    # Implementation would depend on response format
    
    return structured_data

# Validation Prompts

VALIDATION_PROMPTS = {
    "parameter_units": "Verify all water quality parameters have correct units and are within reasonable ranges for the specified water source.",
    
    "treatment_compatibility": "Check that all recommended treatments are compatible with each other and can be operated in the specified sequence.",
    
    "cost_reasonableness": "Validate that cost estimates are reasonable for the specified system size and complexity in the given geographic region.",
    
    "regulatory_compliance": "Confirm that the recommended system meets all applicable local, regional, and national water quality regulations.",
    
    "operational_feasibility": "Assess whether the recommended system can be realistically operated and maintained by available personnel with specified skill levels."
}

def build_treatment_prompt(treatment_specs: dict, customer_context: dict) -> str:
    """Build the complete prompt for treatment recommendation"""
    
    violations = treatment_specs.get('parameters', {})
    
    prompt = f"""
TREATMENT REQUIREMENTS ANALYSIS:

Identified Violations:
"""
    
    for param, details in violations.items():
        if not details.get('compliant', True):
            prompt += f"- {param}: {details.get('value')} (violates standard)\n"
    
    prompt += f"""
Customer Context:
- Location: {customer_context.get('location', 'Not specified')}
- Usage: {customer_context.get('water_usage', 'Not specified')}
- Flow Rate: {customer_context.get('daily_flow_rate', 'Not specified')} L/day
- Budget Constraints: {customer_context.get('budget', 'Not specified')}

Please design a comprehensive treatment system following the treatment selection template, ensuring all violations are addressed with appropriate technologies and sequencing.
"""