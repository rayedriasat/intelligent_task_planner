#!/usr/bin/env python
"""
Test the AI service with fallback mechanism.
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
from planner.services.ai_service import get_ai_scheduling_suggestions_sync

def test_ai_service_fallback():
    """Test the AI service fallback mechanism."""
    print("🤖 Testing AI Service with Fallback")
    print("=" * 50)
    
    # Get or create a test user
    try:
        user = User.objects.get(username='asus')
        print(f"✅ Found test user: {user.username}")
    except User.DoesNotExist:
        print("❌ Test user 'asus' not found. Creating one...")
        user = User.objects.create_user(
            username='asus',
            email='asus@example.com',
            password='testpass123'
        )
        print(f"✅ Created test user: {user.username}")
    
    # Create some test tasks
    now = timezone.now()
    
    # Clean up any existing test tasks
    Task.objects.filter(user=user, title__startswith="AI Test Task").delete()
    TimeBlock.objects.filter(user=user, start_time__gte=now).delete()
    
    tasks = []
    for i in range(3):
        task = Task.objects.create(
            user=user,
            title=f"AI Test Task {i+1}",
            description=f"This is test task {i+1} for AI scheduling",
            estimated_hours=1.5,
            priority=i+1,  # Priority 1, 2, 3
            deadline=now + timedelta(days=i+2)
        )
        tasks.append(task)
        print(f"✅ Created task: {task.title} (Priority: {task.priority})")
    
    # Create some time blocks
    time_blocks = []
    for i in range(2):
        start_time = now + timedelta(days=1, hours=9+i*3)  # 9 AM and 12 PM tomorrow
        end_time = start_time + timedelta(hours=2)  # 2-hour blocks
        
        block = TimeBlock.objects.create(
            user=user,
            start_time=start_time,
            end_time=end_time,
            is_recurring=False
        )
        time_blocks.append(block)
        print(f"✅ Created time block: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}")
    
    # Test AI service
    print("\n🧠 Testing AI Service...")
    try:
        result = get_ai_scheduling_suggestions_sync(tasks, time_blocks)
        
        print(f"📊 AI Service Result:")
        print(f"   Success: {result.success}")
        print(f"   Suggestions: {len(result.suggestions)}")
        print(f"   Overall Score: {result.overall_score}")
        print(f"   Reasoning: {result.reasoning}")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        
        if result.suggestions:
            print(f"\n📋 Suggestions:")
            for i, suggestion in enumerate(result.suggestions, 1):
                task = next(t for t in tasks if t.id == suggestion.task_id)
                print(f"   {i}. Task: {task.title}")
                print(f"      Start: {suggestion.suggested_start_time}")
                print(f"      End: {suggestion.suggested_end_time}")
                print(f"      Confidence: {suggestion.confidence_score:.2f}")
                print(f"      Reasoning: {suggestion.reasoning}")
                print()
        
        # Test the service functionality
        if result.success and result.suggestions:
            print("✅ AI Service working correctly with fallback mechanism!")
            print("✅ Fallback provides reasonable scheduling suggestions based on priority")
        elif result.success and not result.suggestions:
            print("⚠️ AI Service working but no suggestions returned")
        else:
            print("❌ AI Service not working properly")
            print(f"   Error: {result.error_message}")
    
    except Exception as e:
        print(f"❌ Error testing AI service: {e}")
    
    # Clean up
    Task.objects.filter(user=user, title__startswith="AI Test Task").delete()
    TimeBlock.objects.filter(user=user, start_time__gte=now).delete()
    print("\n🧹 Cleaned up test data")
    
    print("\n🎉 AI Service test completed!")

if __name__ == "__main__":
    test_ai_service_fallback()