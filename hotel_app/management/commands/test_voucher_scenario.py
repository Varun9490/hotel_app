from django.core.management.base import BaseCommand
from django.test import TestCase
from django.test.runner import DiscoverRunner
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Run the multi-day voucher scanning test case'

    def handle(self, *args, **options):
        self.stdout.write("🧪 Running multi-day voucher scanning test...")
        
        # Set up test runner
        test_runner = DiscoverRunner(verbosity=2)
        
        # Run the specific test
        failures = test_runner.run_tests([
            "hotel_app.tests.HotelAPITests.test_multi_day_voucher_scanning_scenario"
        ])
        
        if failures:
            self.stdout.write(
                self.style.ERROR(f"❌ Test failed with {failures} failures")
            )
            sys.exit(1)
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Test passed successfully!")
            )