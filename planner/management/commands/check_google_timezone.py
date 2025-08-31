from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from planner.services.google_calendar_service import GoogleCalendarService


class Command(BaseCommand):
    help = 'Check Google account timezone settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user to check Google timezone for',
        )

    def handle(self, *args, **options):
        email = options.get('email', 'aarontaz56@gmail.com')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(f"❌ User {email} not found")
            return
        
        self.stdout.write(f"🔍 Checking Google Calendar timezone for: {email}")
        self.stdout.write("=" * 60)
        
        try:
            service = GoogleCalendarService(user)
            
            # Get primary calendar details
            calendar_info = service.service.calendars().get(calendarId='primary').execute()
            
            self.stdout.write(f"📅 Google Calendar Info:")
            self.stdout.write(f"   Calendar ID: {calendar_info.get('id')}")
            self.stdout.write(f"   Summary: {calendar_info.get('summary')}")
            self.stdout.write(f"   Time Zone: {calendar_info.get('timeZone', 'Not specified')}")
            self.stdout.write(f"   Location: {calendar_info.get('location', 'Not specified')}")
            
            # Check account settings
            settings_info = service.service.settings().list().execute()
            
            self.stdout.write(f"\n⚙️  Google Account Settings:")
            for item in settings_info.get('items', []):
                if item['id'] in ['timezone', 'locale', 'country']:
                    self.stdout.write(f"   {item['id']}: {item.get('value', 'Not set')}")
            
            # Get timezone specifically
            google_timezone = calendar_info.get('timeZone')
            
            from django.conf import settings
            django_timezone = settings.TIME_ZONE
            
            self.stdout.write(f"\n🌍 Timezone Comparison:")
            self.stdout.write(f"   Django app timezone: {django_timezone}")
            self.stdout.write(f"   Google Calendar timezone: {google_timezone}")
            
            if google_timezone != django_timezone:
                self.stdout.write(f"   ⚠️  TIMEZONE MISMATCH DETECTED!")
                self.stdout.write(f"   This explains why dates are being stored incorrectly.")
                self.stdout.write(f"   Solution: Convert times to Google Calendar's timezone")
            else:
                self.stdout.write(f"   ✅ Timezones match")
                
        except Exception as e:
            self.stdout.write(f"❌ Error checking Google Calendar timezone: {e}")
            self.stdout.write(f"   Make sure you have a valid Google Calendar token")
