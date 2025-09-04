import os
import django
import sys

# Add the project directory to the Python path
sys.path.append('c:\\Users\\Barshon\\Desktop\\New folder\\intelligent_task_planner')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intelligent_task_planner.settings')
django.setup()

from django.contrib.auth.models import User
from planner.models import Task
from django.utils import timezone
from datetime import date

# Get user
user = User.objects.get(id=1)
print(f"Testing completion data for user: {user.username}")

# Get completed tasks with completion timestamps
completed_tasks = Task.objects.filter(
    user=user,
    status='completed',
    completed_at__isnull=False
)

print(f"Completed tasks with completion timestamps: {completed_tasks.count()}")

for task in completed_tasks:
    completion_date = task.completed_at.date() if task.completed_at else None
    print(f"- {task.title}: completed on {completion_date}")

# Test if any tasks were completed today
today = date.today()
tasks_completed_today = completed_tasks.filter(completed_at__date=today).count()
print(f"Tasks completed today ({today}): {tasks_completed_today}")