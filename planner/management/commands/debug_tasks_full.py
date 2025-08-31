from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from planner.models import Task
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Check all tasks and calendar filtering'

    def handle(self, *args, **options):
        user = User.objects.first()
        if not user:
            self.stdout.write("No users found")
            return
            
        self.stdout.write(f"User: {user.username}")
        
        # Get ALL tasks
        all_tasks = Task.objects.filter(user=user)
        self.stdout.write(f"Total tasks: {all_tasks.count()}")
        
        for task in all_tasks:
            self.stdout.write(f"\nTask: {task.title}")
            self.stdout.write(f"  ID: {task.id}")
            self.stdout.write(f"  Status: {task.status}")
            self.stdout.write(f"  Start time: {task.start_time}")
            self.stdout.write(f"  End time: {task.end_time}")
            self.stdout.write(f"  Deadline: {task.deadline}")
            self.stdout.write(f"  Created: {task.created_at}")
            self.stdout.write(f"  Updated: {task.updated_at}")
            
        # Test the exact calendar view logic
        self.stdout.write(f"\n=== Calendar View Logic Test ===")
        base_date = timezone.now().date()
        week_start = base_date - timedelta(days=base_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        self.stdout.write(f"Today: {base_date}")
        self.stdout.write(f"Week start: {week_start}")
        self.stdout.write(f"Week end: {week_end}")
        
        # Test the exact filtering used in calendar view
        week_start_dt = timezone.make_aware(datetime.combine(week_start, datetime.min.time()))
        week_end_dt = timezone.make_aware(datetime.combine(week_end, datetime.max.time()))
        
        self.stdout.write(f"Week start datetime: {week_start_dt}")
        self.stdout.write(f"Week end datetime: {week_end_dt}")
        
        scheduled_tasks = user.tasks.filter(
            start_time__gte=week_start_dt,
            start_time__lte=week_end_dt
        ).order_by('start_time')
        
        self.stdout.write(f"Scheduled tasks in week: {scheduled_tasks.count()}")
        
        for task in scheduled_tasks:
            self.stdout.write(f"  - {task.title}: {task.start_time}")
            
        # Test day-by-day
        self.stdout.write(f"\n=== Day by Day Test ===")
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_tasks = [task for task in scheduled_tasks if task.start_time.date() == day]
            self.stdout.write(f"{day} ({day.strftime('%A')}): {len(day_tasks)} tasks")
            for task in day_tasks:
                self.stdout.write(f"  - {task.title} at {task.start_time.time()}")
