from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from planner.models import Task
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Create test unscheduled tasks for debugging calendar display'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to create tasks for (defaults to first user)',
        )

    def handle(self, *args, **options):
        # Get user
        if options['user']:
            try:
                user = User.objects.get(username=options['user'])
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User '{options['user']}' not found"))
                return
        else:
            users = User.objects.all()
            if not users.exists():
                self.stdout.write(self.style.ERROR("No users found. Please create a user first."))
                return
            user = users.first()
        
        self.stdout.write(f"Creating test tasks for user: {user.username}")
        
        # Delete existing unscheduled tasks to start fresh
        existing_unscheduled = user.tasks.filter(start_time__isnull=True)
        count = existing_unscheduled.count()
        existing_unscheduled.delete()
        self.stdout.write(f"Deleted {count} existing unscheduled tasks")
        
        # Create test tasks
        tomorrow = timezone.now() + timedelta(days=1)
        
        test_tasks = [
            {
                'title': 'Complete project documentation',
                'description': 'Write comprehensive docs for the new feature',
                'estimated_hours': 3.0,
                'priority': 1,
                'deadline': tomorrow + timedelta(days=2),
                'status': 'todo'
            },
            {
                'title': 'Code review session', 
                'description': 'Review team pull requests',
                'estimated_hours': 1.5,
                'priority': 2,
                'deadline': tomorrow + timedelta(days=1),
                'status': 'todo'
            },
            {
                'title': 'Team meeting preparation',
                'description': 'Prepare slides and agenda',
                'estimated_hours': 1.0,
                'priority': 2,
                'deadline': tomorrow + timedelta(hours=8),
                'status': 'todo'
            },
            {
                'title': 'URGENT: Bug fix deployment',
                'description': 'Fix critical production bug',
                'estimated_hours': 2.0,
                'priority': 1,
                'deadline': timezone.now() + timedelta(hours=12),  # Due very soon - urgent
                'status': 'todo'
            },
            {
                'title': 'Design wireframes',
                'description': 'Create wireframes for new feature',
                'estimated_hours': 4.0,
                'priority': 3,
                'deadline': tomorrow + timedelta(days=5),
                'status': 'todo'
            }
        ]
        
        created_tasks = []
        for task_data in test_tasks:
            task = Task.objects.create(user=user, **task_data)
            created_tasks.append(task)
            self.stdout.write(f"✓ Created: {task.title} ({task.estimated_hours}h, P{task.priority})")
        
        self.stdout.write(f"\n✨ Created {len(created_tasks)} test unscheduled tasks!")
        
        # Show summary
        all_unscheduled = user.tasks.filter(start_time__isnull=True, status__in=['todo', 'in_progress'])
        self.stdout.write(f"Total unscheduled tasks for {user.username}: {all_unscheduled.count()}")
        
        # Check urgent tasks
        urgent_deadline = timezone.now() + timedelta(days=2)
        urgent_tasks = all_unscheduled.filter(deadline__lte=urgent_deadline)
        self.stdout.write(f"Urgent tasks (due within 2 days): {urgent_tasks.count()}")
