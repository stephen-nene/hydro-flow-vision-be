# File: tools.py
from aiq.builder.function_info import FunctionInfo
from pydantic import BaseModel
from aiq.builder.builder import Builder

from aiq.cli.register_workflow import register_function

class WaterAnalysisInput(BaseModel):
    # docs strings
    """
    This class represents the input data for water analysis.
    It includes the customer request and guideline parameters.
    """
    customer_request: dict
    guideline: dict

class CustomerRequest(BaseModel):
        """
        This class represents the customer's request for water analysis.
        It includes various parameters related to water quality.
        """
        ph: float
        hardness: float
        solids: float
        chloramines: float
        sulfate: float
        conductivity: float
        organic_carbon: float
        trihalomethanes: float
        turbidity: float

class Guideline(BaseModel):
        """
        This class represents the guideline parameters for water analysis.
        It includes the minimum and maximum values for various parameters.
        """
        ph: dict
        hardness: dict
        solids: dict
        chloramines: dict
        sulfate: dict
        conductivity: dict
        organic_carbon: dict
        trihalomethanes: dict
        turbidity: dict

# @register_function(
#     name="analyse_lab_report",
#     description="Analyse the lab report and return the parameter violations",
# )
async def analyse_lab_report(builder: Builder):
    def _analyse(input_data: WaterAnalysisInput):
        # Your existing analysis logic
        violations = {}
        for param, value in input_data.customer_request.items():
            if param in input_data.guideline:
                min_val = input_data.guideline[param]["min"]
                max_val = input_data.guideline[param]["max"]
                if value < min_val or value > max_val:
                    violations[param] = {
                        "value": value,
                        "deviation": "LOW" if value < min_val else "HIGH"
                    }
        return {"parameter_violations": violations}
    
    yield FunctionInfo.from_fn(_analyse)