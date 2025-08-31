from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from planner.models import Task


class Command(BaseCommand):
    help = 'Clear incorrect automatic scheduling and reset tasks to unscheduled'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, help='Username to fix tasks for')
        parser.add_argument('--confirm', action='store_true', help='Actually perform the changes')

    def handle(self, *args, **options):
        if options['user']:
            try:
                user = User.objects.get(username=options['user'])
            except User.DoesNotExist:
                self.stdout.write(f"User '{options['user']}' not found")
                return
        else:
            user = User.objects.first()
            if not user:
                self.stdout.write("No users found")
                return
                
        self.stdout.write(f"Working with user: {user.username}")
        
        # Find all tasks that were auto-scheduled at the same time
        # (likely the incorrect scheduling)
        scheduled_tasks = Task.objects.filter(
            user=user,
            start_time__isnull=False
        )
        
        self.stdout.write(f"Found {scheduled_tasks.count()} scheduled tasks:")
        
        # Group by start time to see the pattern
        time_counts = {}
        for task in scheduled_tasks:
            start_time = task.start_time
            if start_time not in time_counts:
                time_counts[start_time] = []
            time_counts[start_time].append(task)
            
        for start_time, tasks in time_counts.items():
            self.stdout.write(f"  {start_time}: {len(tasks)} tasks")
            for task in tasks:
                self.stdout.write(f"    - {task.title}")
                
        # If multiple tasks have the exact same start time, they're probably incorrectly scheduled
        suspicious_times = [time for time, tasks in time_counts.items() if len(tasks) > 1]
        
        if suspicious_times:
            self.stdout.write(f"\nFound {len(suspicious_times)} suspicious time slots with multiple tasks:")
            
            tasks_to_unschedule = []
            for suspicious_time in suspicious_times:
                self.stdout.write(f"  {suspicious_time}:")
                for task in time_counts[suspicious_time]:
                    self.stdout.write(f"    - {task.title} (ID: {task.id})")
                    tasks_to_unschedule.append(task)
                    
            self.stdout.write(f"\nWould unschedule {len(tasks_to_unschedule)} tasks")
            
            if options['confirm']:
                for task in tasks_to_unschedule:
                    task.start_time = None
                    task.end_time = None
                    task.save()
                    
                self.stdout.write(f"✓ Unscheduled {len(tasks_to_unschedule)} tasks")
                self.stdout.write("Tasks are now unscheduled and will appear in the sidebar.")
                self.stdout.write("Use the calendar interface or Re-optimize button to schedule them properly.")
            else:
                self.stdout.write("\nTo actually perform these changes, run with --confirm")
        else:
            self.stdout.write("\nNo suspicious scheduling found.")
