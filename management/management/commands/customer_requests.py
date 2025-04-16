import random
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from management.models import CustomerRequest, WaterLabReport, WaterLabParameter
from profiles.models import UserRole
from management.models import ReportSource, TestType

User = get_user_model()

# Define Kenyan Locations
KENYAN_LOCATIONS = [
    {"name": "Nairobi", "lat": -1.286389, "lng": 36.817223},
    {"name": "Mombasa", "lat": -4.043477, "lng": 39.668206},
    {"name": "Kisumu", "lat": -0.091702, "lng": 34.767956},
    {"name": "Nakuru", "lat": -0.303099, "lng": 36.080025},
    {"name": "Eldoret", "lat": 0.520360, "lng": 35.269779},
    {"name": "Thika", "lat": -1.033333, "lng": 37.069444},
    {"name": "Nyeri", "lat": -0.420130, "lng": 36.947600},
    {"name": "Garissa", "lat": -0.456944, "lng": 39.658333},
    {"name": "Meru", "lat": 0.047035, "lng": 37.649803},
    {"name": "Kitale", "lat": 1.015800, "lng": 35.006073},
    {"name": "Machakos", "lat": -1.516667, "lng": 37.266667},
    {"name": "Lamu", "lat": -2.271680, "lng": 40.902046},
    {"name": "Naivasha", "lat": -0.716667, "lng": 36.433333},
    {"name": "Isiolo", "lat": 0.354621, "lng": 37.582199},
    {"name": "Wajir", "lat": 1.750000, "lng": 40.050000},
]

# Define Parameter Pool
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

class Command(BaseCommand):
    help = 'Seed CustomerRequest data with Kenyan locations and create WaterLabReports with Parameters'

    def handle(self, *args, **kwargs):
        customers = User.objects.filter(role=UserRole.CUSTOMER)
        staff_users = User.objects.filter(role__in=[UserRole.SUPPORT_STAFF, UserRole.FINANCE_STAFF])

        if not customers.exists() or not staff_users.exists():
            self.stdout.write(self.style.ERROR('Not enough customers or staff to proceed.'))
            return

        for i in range(20):  # Adjust number of requests you want to seed
            customer = random.choice(customers)
            handlers = random.sample(list(staff_users), k=random.randint(2, 5))
            location = random.choice(KENYAN_LOCATIONS)

            # Create CustomerRequest
            request = CustomerRequest.objects.create(
                customer=customer,
                water_source=random.choice(['Borehole', 'River', 'Municipal', 'Rainwater']),
                daily_water_requirement=random.randint(100, 500),
                daily_flow_rate=random.randint(10, 50),
                water_usage=random.choice(['Irrigation', 'Domestic', 'Industrial']),
                site_location={
                    "name": location["name"],
                    "lat": location["lat"],
                    "lng": location["lng"]
                },
                extras={"notes": f"Seeded request {i} with real Kenyan site"},
                budjet={"amount": random.randint(1000, 10000), "currency": "KES"},
                status=random.choice(['pending', 'approved', 'rejected'])
            )
            request.handlers.set(handlers)

            # Create WaterLabReport for each CustomerRequest
            report = WaterLabReport.objects.create(
                customer_request=request,
                report_source=random.choice([choice[0] for choice in ReportSource.choices]),
                report_date=datetime.date.today() - datetime.timedelta(days=random.randint(1, 30)),
                test_type=random.choice([choice[0] for choice in TestType.choices])
            )

            # Create random WaterLabParameters
            params = []
            for param_name, meta in PARAMETER_POOL.items():
                value = round(random.uniform(meta["min_base"], meta["max_base"]), 3)
                params.append(WaterLabParameter(
                    lab_report=report,
                    name=param_name,
                    unit=meta["unit"],
                    value=value
                ))

            # Bulk insert the parameters
            WaterLabParameter.objects.bulk_create(params)

        self.stdout.write(self.style.SUCCESS('✅ Successfully seeded CustomerRequest, WaterLabReport, and Parameters.'))

