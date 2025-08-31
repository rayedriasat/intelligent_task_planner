from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from planner.models import Task
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Debug calendar week calculation'

    def handle(self, *args, **options):
        user = User.objects.first()
        
        # Mimic the calendar view logic exactly
        base_date = timezone.now().date()
        week_start = base_date - timedelta(days=base_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        self.stdout.write(f"Today (timezone.now().date()): {base_date}")
        self.stdout.write(f"Week start: {week_start}")
        self.stdout.write(f"Week end: {week_end}")
        
        # Get user's tasks for this week using the exact same query as calendar
        scheduled_tasks = user.tasks.filter(
            start_time__date__range=[week_start, week_end]
        ).order_by('start_time')
        
        self.stdout.write(f"Tasks in week range {week_start} to {week_end}: {scheduled_tasks.count()}")
        
        # Check all scheduled tasks and their dates
        all_scheduled = user.tasks.filter(start_time__isnull=False)
        self.stdout.write(f"\nAll scheduled tasks:")
        for task in all_scheduled:
            task_date = task.start_time.date()
            self.stdout.write(f"  {task.title}: {task.start_time} -> Date: {task_date}")
            self.stdout.write(f"    In range? {week_start <= task_date <= week_end}")
        
        # Check if timezone conversion is the issue
        self.stdout.write(f"\nTimezone info:")
        self.stdout.write(f"Current timezone setting: {timezone.get_current_timezone()}")
        
        # Test manual date filtering
        self.stdout.write(f"\nManual date tests:")
        import datetime as dt
        aug31 = dt.date(2025, 8, 31)
        self.stdout.write(f"Aug 31 in range? {week_start <= aug31 <= week_end}")
        
        # Test the exact filter
        manual_filter = user.tasks.filter(start_time__date=aug31)
        self.stdout.write(f"Tasks on Aug 31: {manual_filter.count()}")
