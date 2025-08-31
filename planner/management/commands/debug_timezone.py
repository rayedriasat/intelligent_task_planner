from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
import pytz


class Command(BaseCommand):
    help = 'Debug timezone and date conversion issues'

    def handle(self, *args, **options):
        self.stdout.write("🕐 Timezone Debug Information")
        self.stdout.write("=" * 50)
        
        # Current timezone settings
        from django.conf import settings
        self.stdout.write(f"Django TIME_ZONE setting: {settings.TIME_ZONE}")
        self.stdout.write(f"Django USE_TZ setting: {settings.USE_TZ}")
        self.stdout.write(f"Current timezone: {timezone.get_current_timezone()}")
        
        # Current time in different timezones
        now_utc = timezone.now()
        self.stdout.write(f"\nCurrent time (UTC): {now_utc}")
        self.stdout.write(f"Current time (local): {timezone.localtime(now_utc)}")
        
        # Test date conversion
        test_date_str = "September 1, 2025 10:00 AM"
        self.stdout.write(f"\n📅 Testing date: {test_date_str}")
        
        # Simulate creating a datetime for Sep 1
        test_datetime = datetime(2025, 9, 1, 10, 0, 0)
        self.stdout.write(f"Naive datetime: {test_datetime}")
        
        # Make it timezone aware (what Django does)
        aware_datetime = timezone.make_aware(test_datetime)
        self.stdout.write(f"Timezone-aware datetime: {aware_datetime}")
        self.stdout.write(f"In UTC: {aware_datetime.astimezone(pytz.UTC)}")
        
        # What gets sent to Google Calendar
        iso_format = aware_datetime.isoformat()
        self.stdout.write(f"ISO format (sent to Google): {iso_format}")
        
        # Common timezones
        self.stdout.write(f"\n🌍 Common Timezones:")
        common_timezones = ['US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific', 'Europe/London']
        for tz_name in common_timezones:
            tz = pytz.timezone(tz_name)
            local_time = aware_datetime.astimezone(tz)
            self.stdout.write(f"  {tz_name}: {local_time}")
        
        # Check if any tasks exist
        from planner.models import Task
        tasks = Task.objects.filter(start_time__isnull=False)[:3]
        if tasks:
            self.stdout.write(f"\n📋 Sample task times:")
            for task in tasks:
                self.stdout.write(f"  Task: {task.title}")
                self.stdout.write(f"    Start time (stored): {task.start_time}")
                self.stdout.write(f"    Start time (local): {timezone.localtime(task.start_time)}")
                self.stdout.write(f"    ISO format: {task.start_time.isoformat()}")
        else:
            self.stdout.write(f"\n📋 No tasks with start times found")
        
        self.stdout.write(f"\n💡 Recommendations:")
        if settings.TIME_ZONE == 'UTC':
            self.stdout.write(f"   Consider setting TIME_ZONE to your local timezone")
            self.stdout.write(f"   For US Eastern: TIME_ZONE = 'America/New_York'")
            self.stdout.write(f"   For US Pacific: TIME_ZONE = 'America/Los_Angeles'")
        
        self.stdout.write(f"   Current issue: Dates created in local time get converted to UTC")
