"""
Notification service for task reminders and alerts.
Uses Django-Q2 for background task processing.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django_q.tasks import schedule, async_task

from ..models import Task, TaskNotification, NotificationPreference

logger = logging.getLogger(__name__)


class NotificationService:
    """Service class for handling all types of task notifications."""
    
    @staticmethod
    def schedule_task_reminders(task: Task) -> List[TaskNotification]:
        """Schedule notifications for a newly scheduled task."""
        if not task.start_time or not task.user:
            return []
        
        notifications = []
        prefs = NotificationPreference.get_or_create_for_user(task.user)
        
        # Task reminder notification
        if prefs.task_reminder_enabled:
            reminder_time = task.start_time - timedelta(minutes=prefs.task_reminder_minutes)
            
            # Only schedule if reminder time is in the future
            if reminder_time > timezone.now():
                notification = TaskNotification.objects.create(
                    task=task,
                    notification_type='task_reminder',
                    scheduled_time=reminder_time,
                    delivery_method=prefs.task_reminder_method,
                    title=f"Task Starting Soon: {task.title}",
                    message=f"Your task '{task.title}' is scheduled to start in {prefs.task_reminder_minutes} minutes at {task.start_time.strftime('%I:%M %p')}."
                )
                
                # Schedule the notification using Django-Q2
                schedule(
                    'planner.services.notification_service.send_notification',
                    notification.id,
                    schedule_type='O',  # Once
                    next_run=reminder_time
                )
                
                notifications.append(notification)
        
        # Deadline warning notification
        if prefs.deadline_warning_enabled and task.deadline:
            warning_time = task.deadline - timedelta(hours=prefs.deadline_warning_hours)
            
            # Only schedule if warning time is in the future
            if warning_time > timezone.now():
                notification = TaskNotification.objects.create(
                    task=task,
                    notification_type='deadline_warning',
                    scheduled_time=warning_time,
                    delivery_method=prefs.deadline_warning_method,
                    title=f"Deadline Approaching: {task.title}",
                    message=f"Your task '{task.title}' is due in {prefs.deadline_warning_hours} hours at {task.deadline.strftime('%B %d, %Y at %I:%M %p')}."
                )
                
                # Schedule the notification using Django-Q2
                schedule(
                    'planner.services.notification_service.send_notification',
                    notification.id,
                    schedule_type='O',  # Once
                    next_run=warning_time
                )
                
                notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def cancel_task_notifications(task: Task):
        """Cancel pending notifications for a task (when task is rescheduled/deleted)."""
        pending_notifications = TaskNotification.objects.filter(
            task=task,
            status='pending'
        )
        
        for notification in pending_notifications:
            notification.status = 'cancelled'
            notification.save()
        
        logger.info(f"Cancelled {pending_notifications.count()} notifications for task {task.id}")
    
    @staticmethod
    def send_optimization_notification(user: User, message: str):
        """Send a schedule optimization notification."""
        prefs = NotificationPreference.get_or_create_for_user(user)
        
        if not prefs.schedule_optimization_enabled:
            return
        
        # Create a temporary task for the notification (optimization notifications are not task-specific)
        # We'll use the user's first task or create a dummy one
        user_task = user.tasks.first()
        if not user_task:
            return
        
        notification = TaskNotification.objects.create(
            task=user_task,
            notification_type='schedule_optimization',
            scheduled_time=timezone.now(),
            delivery_method=prefs.schedule_optimization_method,
            title="Schedule Optimization Complete",
            message=message
        )
        
        # Send immediately
        async_task('planner.services.notification_service.send_notification', notification.id)
    
    @staticmethod
    def send_pomodoro_break_notification(user: User, break_type: str = 'short'):
        """Send a Pomodoro break notification."""
        prefs = NotificationPreference.get_or_create_for_user(user)
        
        if not prefs.pomodoro_break_enabled:
            return
        
        # Get current active task
        active_task = user.tasks.filter(status='in_progress').first()
        if not active_task:
            return
        
        break_duration = "5 minutes" if break_type == 'short' else "15 minutes"
        
        notification = TaskNotification.objects.create(
            task=active_task,
            notification_type='pomodoro_break',
            scheduled_time=timezone.now(),
            delivery_method='browser',  # Pomodoro notifications are always browser
            title=f"Time for a {break_type.title()} Break!",
            message=f"Great job focusing! Take a {break_duration} break before your next Pomodoro session."
        )
        
        # Send immediately
        async_task('planner.services.notification_service.send_notification', notification.id)


def send_notification(notification_id: int):
    """
    Background task to send a notification.
    This function is called by Django-Q2.
    """
    try:
        notification = TaskNotification.objects.get(id=notification_id)
        
        if notification.status != 'pending':
            logger.warning(f"Notification {notification_id} is not pending, skipping")
            return
        
        user = notification.task.user
        prefs = NotificationPreference.get_or_create_for_user(user)
        
        success = False
        
        # Send browser notification
        if notification.delivery_method in ['browser', 'both'] and prefs.browser_notifications_enabled:
            success |= _send_browser_notification(notification)
        
        # Send email notification
        if notification.delivery_method in ['email', 'both'] and prefs.email_notifications_enabled:
            success |= _send_email_notification(notification)
        
        if success:
            notification.mark_as_sent()
            logger.info(f"Successfully sent notification {notification_id}")
        else:
            notification.mark_as_failed("Failed to send via any method")
            logger.error(f"Failed to send notification {notification_id}")
    
    except TaskNotification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
    except Exception as e:
        logger.error(f"Error sending notification {notification_id}: {str(e)}")
        try:
            notification = TaskNotification.objects.get(id=notification_id)
            notification.mark_as_failed(str(e))
        except:
            pass


def _send_browser_notification(notification: TaskNotification) -> bool:
    """
    Send browser push notification.
    For now, this stores the notification in the database for frontend polling.
    In a production environment, you would integrate with Web Push API.
    """
    try:
        # For now, we'll just mark it as ready for frontend polling
        # In production, you'd use Web Push API here
        logger.info(f"Browser notification ready for {notification.task.user.username}: {notification.title}")
        return True
    except Exception as e:
        logger.error(f"Failed to send browser notification: {str(e)}")
        return False


def _send_email_notification(notification: TaskNotification) -> bool:
    """Send email notification."""
    try:
        user = notification.task.user
        
        # Render email template
        html_message = render_to_string('planner/emails/notification.html', {
            'user': user,
            'notification': notification,
            'task': notification.task,
        })
        
        plain_message = render_to_string('planner/emails/notification.txt', {
            'user': user,
            'notification': notification,
            'task': notification.task,
        })
        
        send_mail(
            subject=notification.title,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email notification sent to {user.email}: {notification.title}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}")
        return False


def schedule_daily_notification_check():
    """
    Schedule a daily task to check for upcoming deadlines and send warnings.
    This should be called from Django management command or app initialization.
    """
    schedule(
        'planner.services.notification_service.check_upcoming_deadlines',
        schedule_type='D',  # Daily
        repeats=-1  # Repeat indefinitely
    )


def check_upcoming_deadlines():
    """
    Background task to check for upcoming deadlines and send notifications.
    Runs daily to catch any missed deadline warnings.
    """
    logger.info("Checking for upcoming deadlines...")
    
    # Get all users with notification preferences
    users_with_prefs = User.objects.filter(
        notification_preferences__deadline_warning_enabled=True
    ).prefetch_related('notification_preferences')
    
    for user in users_with_prefs:
        prefs = user.notification_preferences
        warning_threshold = timezone.now() + timedelta(hours=prefs.deadline_warning_hours)
        
        # Find tasks with upcoming deadlines that don't have notifications yet
        upcoming_tasks = user.tasks.filter(
            deadline__lte=warning_threshold,
            deadline__gt=timezone.now(),
            status__in=['todo', 'in_progress']
        ).exclude(
            notifications__notification_type='deadline_warning',
            notifications__status__in=['pending', 'sent']
        )
        
        for task in upcoming_tasks:
            # Create and send deadline warning
            notification = TaskNotification.objects.create(
                task=task,
                notification_type='deadline_warning',
                scheduled_time=timezone.now(),
                delivery_method=prefs.deadline_warning_method,
                title=f"Deadline Approaching: {task.title}",
                message=f"Your task '{task.title}' is due on {task.deadline.strftime('%B %d, %Y at %I:%M %p')}."
            )
            
            # Send immediately
            async_task('planner.services.notification_service.send_notification', notification.id)
    
    logger.info("Finished checking upcoming deadlines")