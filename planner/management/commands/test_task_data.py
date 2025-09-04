from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from planner.models import Task
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate

class Command(BaseCommand):
    help = 'Test task completion data for consistency report'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, help='User ID to test', default=1)

    def handle(self, *args, **options):
        user_id = options['user_id']
        
        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f"Testing data for user: {user.username} (ID: {user.id})")
            
            # Get all tasks for user
            all_tasks = Task.objects.filter(user=user)
            self.stdout.write(f"Total tasks for user: {all_tasks.count()}")
            
            # Get completed tasks
            completed_tasks = all_tasks.filter(status='completed')
            self.stdout.write(f"Completed tasks: {completed_tasks.count()}")
            
            # Show some recent completed tasks
            recent_completed = completed_tasks.order_by('-updated_at')[:10]
            self.stdout.write("\nRecent completed tasks:")
            for task in recent_completed:
                self.stdout.write(f"- {task.title}: {task.updated_at.date()} (updated_at)")
            
            # Test the query used in the API
            current_year = timezone.now().year
            self.stdout.write(f"\nTesting for current year: {current_year}")
            
            # Test with year lookup instead of date range
            completed_tasks_current_year = completed_tasks.filter(
                updated_at__year=current_year
            )
            
            self.stdout.write(f"Completed tasks in {current_year} (year lookup): {completed_tasks_current_year.count()}")
            
            # Also test with 2025 specifically
            completed_tasks_2025 = completed_tasks.filter(
                updated_at__year=2025
            )
            
            self.stdout.write(f"Completed tasks in 2025 (year lookup): {completed_tasks_2025.count()}")
            
            # Test creating some sample completed tasks for today
            if completed_tasks.count() == 0:
                self.stdout.write("\nNo completed tasks found. Creating sample data...")
                
                # Create a few sample completed tasks
                for i in range(5):
                    Task.objects.create(
                        user=user,
                        title=f"Sample Task {i+1}",
                        description=f"This is a sample task {i+1} for testing",
                        deadline=timezone.now() + timedelta(days=1),
                        priority=2,
                        estimated_hours=1.0,
                        status='completed'
                    )
                
                self.stdout.write("Created 5 sample completed tasks")
                
        except User.DoesNotExist:
            self.stdout.write(f"User with ID {user_id} not found")
            self.stdout.write("Available users:")
            for user in User.objects.all()[:5]:
                self.stdout.write(f"- {user.username} (ID: {user.id})")