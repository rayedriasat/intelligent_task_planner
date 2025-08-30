#!/usr/bin/env python
"""
Test script for notification system functionality.
"""
import os
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intelligent_task_planner.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from planner.models import Task, NotificationPreference
from planner.services.notification_service import NotificationService

def test_notification_system():
    """Test the notification system end-to-end."""
    print("🧪 Testing Notification System")
    print("=" * 50)
    
    # Get or create a test user
    try:
        user = User.objects.get(username='asus')
        print(f"✅ Found test user: {user.username}")
    except User.DoesNotExist:
        print("❌ Test user 'asus' not found. Please create a user first.")
        return
    
    # Check notification preferences
    prefs = NotificationPreference.get_or_create_for_user(user)
    print(f"✅ Notification preferences loaded for {user.username}")
    print(f"   - Task reminders: {'Enabled' if prefs.task_reminder_enabled else 'Disabled'}")
    print(f"   - Email notifications: {'Enabled' if prefs.email_notifications_enabled else 'Disabled'}")
    
    # Create a test task with start time in the future
    future_time = timezone.now() + timedelta(hours=1)
    task = Task.objects.create(
        user=user,
        title="Test Notification Task",
        description="This task is for testing the notification system",
        estimated_hours=1.0,
        priority=2,
        deadline=timezone.now() + timedelta(days=1),
        start_time=future_time,
        end_time=future_time + timedelta(hours=1)
    )
    print(f"✅ Created test task: {task.title}")
    print(f"   - Scheduled for: {task.start_time}")
    
    # Test notification scheduling
    try:
        notifications = NotificationService.schedule_task_reminders(task)
        print(f"✅ Scheduled {len(notifications)} notifications for the task")
        
        for notification in notifications:
            print(f"   - {notification.notification_type}: {notification.title}")
    except Exception as e:
        print(f"❌ Error scheduling notifications: {e}")
    
    # Test optimization notification
    try:
        NotificationService.send_optimization_notification(
            user,
            "Test optimization notification - notification system is working!"
        )
        print("✅ Sent test optimization notification")
    except Exception as e:
        print(f"❌ Error sending optimization notification: {e}")
    
    # Check pending notifications in database
    from planner.models import TaskNotification
    pending_notifications = TaskNotification.objects.filter(
        task__user=user,
        status='pending'
    ).count()
    
    sent_notifications = TaskNotification.objects.filter(
        task__user=user,
        status='sent'
    ).count()
    
    print(f"📊 Notification Status:")
    print(f"   - Pending notifications: {pending_notifications}")
    print(f"   - Sent notifications: {sent_notifications}")
    
    # Clean up test task
    task.delete()
    print("🧹 Cleaned up test task")
    
    print("\n🎉 Notification system test completed!")

if __name__ == "__main__":
    test_notification_system()