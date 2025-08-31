from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from planner.services.google_calendar_service import GoogleCalendarService
from planner.models import GoogleCalendarIntegration


class Command(BaseCommand):
    help = 'Test Google Calendar integration credentials'

    def handle(self, *args, **options):
        user = User.objects.first()
        if not user:
            self.stdout.write("No users found")
            return
            
        self.stdout.write(f"Testing Google Calendar integration for user: {user.username}")
        
        # Check integration status
        integration = GoogleCalendarIntegration.objects.filter(user=user).first()
        if not integration:
            self.stdout.write("❌ No Google Calendar integration found")
            return
            
        self.stdout.write(f"✅ Integration found: {integration.calendar_id}")
        self.stdout.write(f"✅ Enabled: {integration.is_enabled}")
        
        # Test service initialization
        try:
            service = GoogleCalendarService(user)
            self.stdout.write("✅ Google Calendar service initialized successfully")
            
            if service.service:
                self.stdout.write("✅ Google API service is available")
                
                # Test calendar access
                try:
                    calendar = service.service.calendars().get(calendarId='primary').execute()
                    self.stdout.write(f"✅ Can access primary calendar: {calendar.get('summary', 'Unknown')}")
                except Exception as e:
                    self.stdout.write(f"❌ Calendar access failed: {e}")
            else:
                self.stdout.write("❌ Google API service is not available")
                
        except Exception as e:
            self.stdout.write(f"❌ Service initialization failed: {e}")
            
        self.stdout.write("\n📝 Manual scheduling should now work with Google Calendar sync!")
