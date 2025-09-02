from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import logging

from ..models import NotificationPreference

logger = logging.getLogger(__name__)


class NotificationPreferencesView(LoginRequiredMixin, UpdateView):
    """View for managing user notification preferences."""
    model = NotificationPreference
    template_name = 'planner/notification_preferences.html'
    fields = [
        'task_reminder_enabled', 'task_reminder_minutes', 'task_reminder_method',
        'deadline_warning_enabled', 'deadline_warning_hours', 'deadline_warning_method',
        'schedule_optimization_enabled', 'schedule_optimization_method',
        'pomodoro_break_enabled',
        'email_notifications_enabled', 'browser_notifications_enabled'
    ]
    success_url = reverse_lazy('planner:notification_preferences')
    
    def get_object(self, queryset=None):
        """Get or create notification preferences for the current user."""
        from ..models import NotificationPreference
        return NotificationPreference.get_or_create_for_user(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Notification preferences updated successfully!')
        return super().form_valid(form)


@login_required
def get_notifications(request):
    """API endpoint to get pending notifications for the current user."""
    try:
        from ..models import TaskNotification
        
        # Get recent notifications (sent in the last 24 hours) for display
        recent_notifications = TaskNotification.objects.filter(
            task__user=request.user,
            status='sent',
            sent_time__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-sent_time')[:10]
        
        notifications_data = []
        for notification in recent_notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'created_at': notification.sent_time.isoformat(),
                'is_read': False,  # We'll add read tracking later
                'task': {
                    'id': notification.task.id,
                    'title': notification.task.title,
                } if notification.task else None
            })
        
        # For now, assume all notifications are unread
        unread_count = len(notifications_data)
        
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'unread_count': unread_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def mark_notification_read(request):
    """Mark a notification as read."""
    try:
        from ..models import TaskNotification
        
        notification_id = request.POST.get('notification_id')
        notification = get_object_or_404(
            TaskNotification,
            id=notification_id,
            task__user=request.user
        )
        
        # For now, we don't have a 'read' status, but we could add one
        # This endpoint exists for future expansion
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def test_notification(request):
    """Test notification system by sending a test notification."""
    try:
        from ..services.notification_service import NotificationService
        
        # Send a test optimization notification
        NotificationService.send_optimization_notification(
            request.user,
            "This is a test notification to verify your notification settings are working correctly."
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Test notification sent! Check your email and browser notifications.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
