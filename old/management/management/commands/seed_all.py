from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Run all seed scripts"

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting full seed process...")

        try:
            call_command('users')
            call_command('water_guidelines')
            call_command('customer_requests')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error while seeding: {e}"))
            return

        self.stdout.write(self.style.SUCCESS("✅ All seeds completed successfully!"))
