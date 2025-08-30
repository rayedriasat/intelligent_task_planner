#!/usr/bin/env python
"""
Test script to verify the fixed time blocks query.
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

def test_fixed_query():
    """Test the fixed time blocks query."""
    print("🔧 Testing Fixed Time Blocks Query")
    print("=" * 50)
    
    # Get user
    try:
        user = User.objects.get(username='asus')
        print(f"✅ Found user: {user.username}")
    except User.DoesNotExist:
        print("❌ User 'asus' not found.")
        return
    
    # Time window
    start_date = timezone.now()
    end_date = start_date + timedelta(days=7)
    
    print(f"\n📅 Query window:")
    print(f"   From: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   To: {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Old query (restrictive)
    old_query_blocks = list(user.time_blocks.filter(
        start_time__gte=start_date,
        end_time__lte=end_date
    ))
    
    # New query (overlapping)
    new_query_blocks = list(user.time_blocks.filter(
        start_time__lt=end_date,    # Block starts before window ends
        end_time__gt=start_date     # Block ends after window starts
    ))
    
    print(f"\n📊 Query Results:")
    print(f"   Old restrictive query: {len(old_query_blocks)} blocks")
    print(f"   New overlapping query: {len(new_query_blocks)} blocks")
    
    print(f"\n📋 Blocks found by new query:")
    for block in new_query_blocks:
        overlap_start = max(block.start_time, start_date)
        overlap_end = min(block.end_time, end_date)
        overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600
        
        print(f"   • {block.start_time.strftime('%a %m/%d %H:%M')} - {block.end_time.strftime('%H:%M')}")
        print(f"     Overlap: {overlap_hours:.1f} hours")
    
    # Test the AI endpoint simulation
    print(f"\n🤖 Simulating AI endpoint with new query...")
    
    unscheduled_tasks = list(user.tasks.filter(
        start_time__isnull=True,
        status__in=['todo', 'in_progress']
    ))
    
    if not unscheduled_tasks:
        print("   ❌ No unscheduled tasks found")
        return
    
    if not new_query_blocks:
        print("   ❌ No available time blocks found for the next 7 days (STILL FAILING)")
        return
    
    print(f"   ✅ Found {len(unscheduled_tasks)} unscheduled tasks")
    print(f"   ✅ Found {len(new_query_blocks)} available time blocks")
    print("   ✅ AI suggestions should work now!")
    
    # Actually test the AI service
    from planner.services.ai_service import get_ai_scheduling_suggestions_sync
    
    result = get_ai_scheduling_suggestions_sync(unscheduled_tasks, new_query_blocks)
    
    print(f"\n📊 AI Service Result:")
    print(f"   Success: {result.success}")
    print(f"   Suggestions: {len(result.suggestions)}")
    print(f"   Overall Score: {result.overall_score}")
    
    if result.error_message:
        print(f"   Error: {result.error_message}")
    else:
        print("   ✅ No errors!")

if __name__ == "__main__":
    test_fixed_query()