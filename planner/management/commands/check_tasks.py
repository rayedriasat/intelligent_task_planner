from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from planner.models import Task
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Check task data for debugging calendar display'

    def handle(self, *args, **options):
        users = User.objects.all()
        self.stdout.write(f"Users: {list(users)}")
        
        if users.exists():
            user = users.first()
            self.stdout.write(f"Working with user: {user.username}")
            
            # Get all tasks for this user
            tasks = Task.objects.filter(user=user)
            self.stdout.write(f"Total tasks: {tasks.count()}")
            
            # Check tasks with start_time
            scheduled_tasks = tasks.filter(start_time__isnull=False)
            self.stdout.write(f"Scheduled tasks: {scheduled_tasks.count()}")
            
            # Show details of scheduled tasks
            for task in scheduled_tasks[:10]:  # First 10
                self.stdout.write(f"Task: {task.title}")
                self.stdout.write(f"  Start time: {task.start_time}")
                if task.start_time:
                    self.stdout.write(f"  Date: {task.start_time.date()}")
                    self.stdout.write(f"  Hour: {task.start_time.hour}")
                self.stdout.write("---")
                
            # Check current week range
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            self.stdout.write(f"Current week: {week_start} to {week_end}")
            
            # Check tasks in current week
            current_week_tasks = tasks.filter(start_time__date__range=[week_start, week_end])
            self.stdout.write(f"Tasks in current week: {current_week_tasks.count()}")
            
            # Check unscheduled tasks
            unscheduled_tasks = tasks.filter(start_time__isnull=True)
            self.stdout.write(f"Unscheduled tasks: {unscheduled_tasks.count()}")
            for task in unscheduled_tasks[:5]:
                self.stdout.write(f"Unscheduled: {task.title} - Deadline: {task.deadline}")
                
        else:
            self.stdout.write("No users found")
