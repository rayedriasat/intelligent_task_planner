#!/usr/bin/env python3
"""
Final demo optimization script
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intelligent_task_planner.settings')
django.setup()

from planner.services.scheduling_engine import SchedulingEngine
from django.contrib.auth.models import User

def main():
    user = User.objects.get(username='the')
    engine = SchedulingEngine(user)
    
    print("🤖 Running final optimization...")
    result = engine.reschedule_week()
    
    scheduled_count = user.tasks.filter(start_time__isnull=False).count()
    unscheduled_count = user.tasks.filter(start_time__isnull=True, status__in=['todo', 'in_progress']).count()
    
    print(f"✅ Optimization complete!")
    print(f"   Scheduled tasks: {scheduled_count}")
    print(f"   Unscheduled tasks: {unscheduled_count}")
    
    # Show next scheduled tasks
    upcoming = user.tasks.filter(
        start_time__isnull=False, 
        status__in=['todo', 'in_progress']
    ).order_by('start_time')[:5]
    
    print("\n📅 Next Scheduled Tasks:")
    for task in upcoming:
        start_str = task.start_time.strftime('%a %m/%d %H:%M')
        end_str = task.end_time.strftime('%H:%M') 
        priority_text = {1: 'Low', 2: 'Med', 3: 'High', 4: 'Urgent'}[task.priority]
        print(f"   - {task.title[:35]}... | {start_str}-{end_str} (P{task.priority}-{priority_text})")
    
    print("\n🎯 DEMO READY FOR PRESENTATION!")

if __name__ == '__main__':
    main()