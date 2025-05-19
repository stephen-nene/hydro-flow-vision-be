from django.core.management.base import BaseCommand
from profiles.models import User, UserRole, UserStatus, Gender
from django.utils.crypto import get_random_string
from faker import Faker
import random

fake = Faker()

class Command(BaseCommand):
    help = 'Seed 5 users per role into the database'

    def handle(self, *args, **kwargs):
        roles = UserRole.choices
        genders = [Gender.MALE, Gender.FEMALE, Gender.NON_BINARY, Gender.UNDISCLOSED]
        status_choices = [UserStatus.ACTIVE, UserStatus.INACTIVE, UserStatus.PENDING_VERIFICATION]

        for role_value, role_name in roles:
            for i in range(5):
                first_name = fake.first_name()
                last_name = fake.last_name()
                username = f"{role_value}_{i}"
                # username = f"{role_value}_{i}_{get_random_string(5)}"
                email = f"{username}@example.com"
                phone = fake.phone_number()

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password="Pass1234!",
                    first_name=first_name,
                    last_name=last_name,
                    role=role_value,
                    status=random.choice(status_choices),
                    date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=65),
                    gender=random.choice(genders),
                    phone_number=fake.phone_number(),
                    address={
                        "street": fake.street_address(),
                        "city": fake.city(),
                        "state": fake.state(),
                        "zip": fake.zipcode(),
                        "country": fake.country()
                    }
                )
                self.stdout.write(self.style.SUCCESS(f"Created user: {user.username} ({role_name})"))

        self.stdout.write(self.style.SUCCESS("Successfully seeded users."))

