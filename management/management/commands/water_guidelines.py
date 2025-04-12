import random
from django.core.management.base import BaseCommand
from management.models import WaterGuideline, WaterGuidelineParameter
from faker import Faker

fake = Faker()

# Parameter definitions with base values and units.
PARAMETER_POOL = {
    "pH": {"unit": "", "min_base": 6.5, "max_base": 8.5},
    "Total Dissolved Solids (TDS)": {"unit": "mg/L", "min_base": 0, "max_base": 1000},
    "Turbidity": {"unit": "NTU", "min_base": 0, "max_base": 5},
    "Iron": {"unit": "mg/L", "min_base": 0, "max_base": 0.3},
    "Electrical Conductivity": {"unit": "μS/cm", "min_base": 0, "max_base": 1400},
    "Chlorine": {"unit": "mg/L", "min_base": 0.2, "max_base": 5},
    "Nitrate": {"unit": "mg/L", "min_base": 0, "max_base": 50},
    "Lead": {"unit": "mg/L", "min_base": 0, "max_base": 0.01},
    "Sodium": {"unit": "mg/L", "min_base": 0, "max_base": 200},
    "Fluoride": {"unit": "mg/L", "min_base": 0.5, "max_base": 1.5},
    "Alkalinity": {"unit": "mg/L", "min_base": 20, "max_base": 200},
    "Hardness": {"unit": "mg/L", "min_base": 0, "max_base": 300},
}

# Regulatory bodies along with distinct usage categories.
BODIES_USAGE = {
    "WHO": ["drinking", "recreational", "domestic"],
    "KEBS": ["bottling", "packaged", "municipal"],
    "EPA": ["domestic", "industrial", "environmental"],
    "EU Drinking Water Directive": ["drinking", "recreational", "institutional"],
    "BIS": ["industrial", "agricultural", "domestic"],
    "FAO": ["irrigation", "agricultural", "domestic"],
    "Health Canada": ["drinking", "recreational", "environmental"],
    "NSW Health": ["cleaning", "disinfection", "domestic"],
    "SABS": ["construction", "municipal", "domestic"],
    "ISO": ["general safety", "drinking", "industrial"],
}

# Choices for guideline status.
STATUS_CHOICES = ["active", "inactive"]

class Command(BaseCommand):
    help = "Seed water guideline data with various usage categories, descriptions, statuses, and parameters."

    def handle(self, *args, **kwargs):
        total_guidelines = 0
        total_parameters = 0
        
        for body, usages in BODIES_USAGE.items():
            self.stdout.write(f"Seeding guidelines for regulatory body: {body}")
            for usage in usages:
                # Create a water guideline with random description and status.
                guideline = WaterGuideline.objects.create(
                    body=body,
                    usage=usage,
                    description=fake.paragraph(nb_sentences=5),
                    status=random.choice(STATUS_CHOICES)
                )
                total_guidelines += 1

                # For each guideline, assign between 10 and 12 distinct parameters.
                num_params = random.randint(10, 12)
                available_params = list(PARAMETER_POOL.keys())
                # Ensure we only sample as many as available.
                param_names = random.sample(available_params, k=min(num_params, len(available_params)))
                
                for name in param_names:
                    definition = PARAMETER_POOL[name]
                    unit = definition["unit"]
                    base_min = definition["min_base"]
                    base_max = definition["max_base"]

                    # Apply slight randomness: use multipliers to vary the base values.
                    min_multiplier = random.uniform(0.9, 1.0)
                    max_multiplier = random.uniform(1.0, 1.1)
                    min_value = round(base_min * min_multiplier, 2) if base_min else 0
                    max_value = round(base_max * max_multiplier, 2) if base_max else 0

                    if min_value > max_value:
                        min_value, max_value = max_value, min_value

                    WaterGuidelineParameter.objects.create(
                        guideline=guideline,
                        name=name,
                        unit=unit,
                        min_value=min_value,
                        max_value=max_value,
                    )
                    total_parameters += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {total_guidelines} guidelines with a total of {total_parameters} parameters."
        ))
