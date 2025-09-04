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
    completion_datetime = task.completed_at
    print(f"- {task.title}: completed on {completion_date} at {completion_datetime}")

# Test if any tasks were completed today with exact date comparison
today = date.today()
print(f"Today's date: {today}")

# Manual check
tasks_today = []
for task in completed_tasks:
    if task.completed_at and task.completed_at.date() == today:
        tasks_today.append(task)

print(f"Tasks completed today (manual check): {len(tasks_today)}")

# Query check
tasks_completed_today = completed_tasks.filter(completed_at__date=today)
print(f"Tasks completed today (query): {tasks_completed_today.count()}")

# Get the actual dates that do exist
from django.db.models.functions import TruncDate
dates_with_completions = completed_tasks.annotate(
    completion_date=TruncDate('completed_at')
).values_list('completion_date', flat=True).distinct()

print(f"Completion dates found: {list(dates_with_completions)}")

# Test the API query pattern
completion_data = completed_tasks.filter(
    completed_at__year=2025
).annotate(
    completion_date=TruncDate('completed_at')
).values('completion_date').annotate(
    tasks_completed=django.db.models.Count('id')
).order_by('completion_date')

print(f"API-style query results:")
for item in completion_data:
    print(f"  {item['completion_date']}: {item['tasks_completed']} tasks")