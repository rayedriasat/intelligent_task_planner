#!/usr/bin/env python
"""
Diagnostic script to check user's time blocks and create default availability.
"""
import os
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intelligent_task_planner.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from planner.models import Task, TimeBlock

def diagnose_time_blocks():
    """Diagnose and fix time block availability issues."""
    print("🔍 Diagnosing Time Block Availability Issues")
    print("=" * 60)
    
    # Get or create a test user
    try:
        user = User.objects.get(username='asus')
        print(f"✅ Found user: {user.username}")
    except User.DoesNotExist:
        print("❌ User 'asus' not found. Please create a user first.")
        return
    
    # Check current time blocks
    now = timezone.now()
    seven_days_later = now + timedelta(days=7)
    
    print(f"\n📅 Checking time blocks for next 7 days:")
    print(f"   From: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   To: {seven_days_later.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get all time blocks for user
    all_blocks = TimeBlock.objects.filter(user=user)
    print(f"\n📊 Total time blocks for user: {all_blocks.count()}")
    
    if all_blocks.exists():
        print("\n📋 Existing time blocks:")
        for block in all_blocks:
            print(f"   • {block.start_time} - {block.end_time}")
            print(f"     Recurring: {block.is_recurring}, Day of week: {block.day_of_week}")
    
    # Check time blocks for next 7 days
    future_blocks = TimeBlock.objects.filter(
        user=user,
        start_time__gte=now,
        end_time__lte=seven_days_later
    )
    
    print(f"\n🔮 Time blocks in next 7 days: {future_blocks.count()}")
    
    if future_blocks.exists():
        for block in future_blocks:
            print(f"   • {block.start_time} - {block.end_time}")
    else:
        print("   ❌ No time blocks found for the next 7 days!")
        print("\n💡 This is why AI suggestions are failing.")
    
    # Check tasks that need scheduling
    unscheduled_tasks = Task.objects.filter(
        user=user,
        start_time__isnull=True,
        status__in=['todo', 'in_progress']
    )
    
    print(f"\n📝 Unscheduled tasks: {unscheduled_tasks.count()}")
    for task in unscheduled_tasks:
        print(f"   • {task.title} ({task.estimated_hours}h, Priority: {task.priority})")
    
    # Offer to create default availability
    if not future_blocks.exists():
        print(f"\n🔧 Creating default availability for the next 7 days...")
        
        created_blocks = []
        
        for day_offset in range(7):
            target_date = (now.date() + timedelta(days=day_offset))
            
            # Skip weekends for default work hours
            if target_date.weekday() < 5:  # Monday = 0, Friday = 4
                # Morning block: 9 AM - 12 PM
                morning_start = timezone.make_aware(
                    datetime.combine(target_date, datetime.min.time().replace(hour=9))
                )
                morning_end = timezone.make_aware(
                    datetime.combine(target_date, datetime.min.time().replace(hour=12))
                )
                
                # Only create if it's in the future
                if morning_end > now:
                    morning_block = TimeBlock.objects.create(
                        user=user,
                        start_time=max(morning_start, now),  # Don't create blocks in the past
                        end_time=morning_end,
                        is_recurring=False
                    )
                    created_blocks.append(morning_block)
                
                # Afternoon block: 1 PM - 5 PM
                afternoon_start = timezone.make_aware(
                    datetime.combine(target_date, datetime.min.time().replace(hour=13))
                )
                afternoon_end = timezone.make_aware(
                    datetime.combine(target_date, datetime.min.time().replace(hour=17))
                )
                
                if afternoon_end > now:
                    afternoon_block = TimeBlock.objects.create(
                        user=user,
                        start_time=max(afternoon_start, now),
                        end_time=afternoon_end,
                        is_recurring=False
                    )
                    created_blocks.append(afternoon_block)
        
        print(f"✅ Created {len(created_blocks)} default time blocks:")
        for block in created_blocks:
            print(f"   • {block.start_time.strftime('%a %Y-%m-%d %H:%M')} - {block.end_time.strftime('%H:%M')}")
    
    # Test AI suggestions again
    if unscheduled_tasks.exists() and (future_blocks.exists() or created_blocks):
        print(f"\n🤖 Testing AI suggestions now...")
        
        from planner.services.ai_service import get_ai_scheduling_suggestions_sync
        
        # Get fresh time blocks
        available_blocks = TimeBlock.objects.filter(
            user=user,
            start_time__gte=now,
            end_time__lte=seven_days_later
        )
        
        result = get_ai_scheduling_suggestions_sync(
            list(unscheduled_tasks[:3]),  # Test with first 3 tasks
            list(available_blocks)
        )
        
        print(f"📊 AI Service Result:")
        print(f"   Success: {result.success}")
        print(f"   Suggestions: {len(result.suggestions)}")
        print(f"   Overall Score: {result.overall_score}")
        print(f"   Reasoning: {result.reasoning}")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        
        if result.suggestions:
            print(f"\n📋 AI Suggestions:")
            for i, suggestion in enumerate(result.suggestions, 1):
                task = next(t for t in unscheduled_tasks if t.id == suggestion.task_id)
                print(f"   {i}. {task.title}")
                print(f"      Time: {suggestion.suggested_start_time} - {suggestion.suggested_end_time}")
                print(f"      Confidence: {suggestion.confidence_score:.2f}")
                print(f"      Reasoning: {suggestion.reasoning}")
                print()
    
    print(f"\n🎯 Summary:")
    print(f"   • User has {all_blocks.count()} total time blocks")
    print(f"   • {future_blocks.count() if not 'created_blocks' in locals() else future_blocks.count() + len(created_blocks)} time blocks available in next 7 days")
    print(f"   • {unscheduled_tasks.count()} tasks need scheduling")
    print(f"   • AI suggestions should now work properly!")

if __name__ == "__main__":
    diagnose_time_blocks()