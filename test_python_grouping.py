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
from django.db import connection

# Check database backend
print(f"Database backend: {connection.vendor}")

# Get user
user = User.objects.get(id=1)

# Get completed tasks with completion timestamps
completed_tasks = Task.objects.filter(
    user=user,
    status='completed',
    completed_at__isnull=False
)

# Try a simpler approach - use Python date extraction instead of database functions
completion_dates = {}
for task in completed_tasks:
    if task.completed_at:
        date_key = task.completed_at.date().strftime('%Y-%m-%d')
        completion_dates[date_key] = completion_dates.get(date_key, 0) + 1

print(f"Completion dates (Python approach):")
for date_str, count in completion_dates.items():
    print(f"  {date_str}: {count} tasks")

# Test the API simulation with Python date grouping
calendar_data = []
today = date.today()
year = today.year

# Create 365 day calendar
from datetime import timedelta
start_date = date(year, 1, 1)
end_date = date(year, 12, 31)

current_date = start_date
while current_date <= end_date:
    date_str = current_date.strftime('%Y-%m-%d')
    tasks_completed = completion_dates.get(date_str, 0)
    calendar_data.append({
        'date': date_str,
        'tasksCompleted': tasks_completed
    })
    current_date += timedelta(days=1)

# Show some data around today
today_str = today.strftime('%Y-%m-%d')
print(f"\nData around today ({today_str}):")
for item in calendar_data:
    if item['tasksCompleted'] > 0:
        print(f"  {item['date']}: {item['tasksCompleted']} tasks")

print(f"\nToday's data: {[item for item in calendar_data if item['date'] == today_str]}")

total_tasks_in_calendar = sum(item['tasksCompleted'] for item in calendar_data)
print(f"Total tasks in calendar: {total_tasks_in_calendar}")