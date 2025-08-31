from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, date


class Command(BaseCommand):
    help = 'Test date conversion after timezone fix'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-date',
            type=str,
            default='2025-09-01',
            help='Date to test in YYYY-MM-DD format',
        )

    def handle(self, *args, **options):
        test_date_str = options['test_date']
        
        self.stdout.write(f"🧪 Testing date conversion: {test_date_str}")
        self.stdout.write("=" * 50)
        
        # Current timezone settings
        from django.conf import settings
        self.stdout.write(f"Django TIME_ZONE: {settings.TIME_ZONE}")
        self.stdout.write(f"Current timezone: {timezone.get_current_timezone()}")
        
        # Parse the test date
        try:
            test_date = datetime.strptime(test_date_str, '%Y-%m-%d').date()
            self.stdout.write(f"Test date (date object): {test_date}")
            
            # Create datetime for 10:00 AM
            test_datetime = datetime.combine(test_date, datetime.min.time().replace(hour=10))
            self.stdout.write(f"Test datetime (naive): {test_datetime}")
            
            # Make timezone aware
            aware_datetime = timezone.make_aware(test_datetime)
            self.stdout.write(f"Test datetime (aware): {aware_datetime}")
            
            # ISO format (what gets sent to Google)
            iso_format = aware_datetime.isoformat()
            self.stdout.write(f"ISO format: {iso_format}")
            
            # Test if this looks correct
            if test_date_str in iso_format:
                self.stdout.write("✅ Date is preserved correctly!")
            else:
                self.stdout.write("❌ Date is being shifted!")
                
        except ValueError as e:
            self.stdout.write(f"❌ Invalid date format: {e}")
            return
        
        # Test with a sample task if any exist
        from planner.models import Task
        sample_task = Task.objects.filter(start_time__isnull=False).first()
        
        if sample_task:
            self.stdout.write(f"\n📋 Sample task test:")
            self.stdout.write(f"Task: {sample_task.title}")
            self.stdout.write(f"Stored start_time: {sample_task.start_time}")
            self.stdout.write(f"ISO format: {sample_task.start_time.isoformat()}")
            
            # Test the Google Calendar conversion
            try:
                from planner.services.google_calendar_service import GoogleCalendarService
                from django.contrib.auth.models import User
                
                # Find a user with Google integration
                user = User.objects.filter(
                    socialaccount__provider='google'
                ).first()
                
                if user:
                    service = GoogleCalendarService(user)
                    event_data = service._task_to_event(sample_task)
                    
                    self.stdout.write(f"\n🔄 Google Calendar event data:")
                    self.stdout.write(f"Start: {event_data['start']}")
                    self.stdout.write(f"End: {event_data['end']}")
                else:
                    self.stdout.write(f"No user with Google integration found")
                    
            except Exception as e:
                self.stdout.write(f"Error testing Google Calendar conversion: {e}")
        else:
            self.stdout.write(f"\n📋 No tasks found to test with")
