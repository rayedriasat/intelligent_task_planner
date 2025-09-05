from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import json
import logging

from .models import Task
from .services.google_calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)


@login_required
@require_POST
def manual_schedule_task(request):
    """Manually schedule a task to a specific time slot"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        date_str = data.get('date')  # YYYY-MM-DD
        
        # Handle both legacy hour-only format and new time format
        if 'time' in data:
            time_str = data.get('time')  # HH:MM format
            # Parse the date and time
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            start_datetime = timezone.make_aware(
                datetime.combine(date_obj, time_obj)
            )
        else:
            # Legacy format - hour only (for backward compatibility)
            hour = int(data.get('hour'))  # 6-24
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_datetime = timezone.make_aware(
                datetime.combine(date_obj, datetime.min.time().replace(hour=hour))
            )
        
        # Get the task
        task = get_object_or_404(Task, id=task_id, user=request.user)
        
        # Calculate end time based on estimated hours
        estimated_hours = float(task.estimated_hours or 1.0)
        end_datetime = start_datetime + timedelta(hours=estimated_hours)
        
        # Check for conflicts
        conflicting_tasks = Task.objects.filter(
            user=request.user,
            start_time__lt=end_datetime,
            end_time__gt=start_datetime
        ).exclude(id=task.id)
        
        if conflicting_tasks.exists():
            return JsonResponse({
                'success': False,
                'error': f'Time slot conflicts with: {", ".join([t.title for t in conflicting_tasks])}'
            })
        
        # Update task with new schedule
        with transaction.atomic():
            task.start_time = start_datetime
            task.end_time = end_datetime
            task.save()
            
            # Sync to Google Calendar if enabled
            try:
                service = GoogleCalendarService(request.user)
                # Check if service has Google integration
                from .models import GoogleCalendarIntegration
                integration = GoogleCalendarIntegration.objects.filter(user=request.user).first()
                if integration and integration.is_enabled and service.service:
                    service.sync_task_to_google(task)
            except Exception as e:
                logger.warning(f"Google Calendar sync failed: {e}")
        
        return JsonResponse({
            'success': True,
            'message': f'Task "{task.title}" scheduled for {start_datetime.strftime("%B %d at %I:%M %p")}',
            'task': {
                'id': task.id,
                'title': task.title,
                'start_time': start_datetime.isoformat(),
                'end_time': end_datetime.isoformat(),
                'estimated_hours': estimated_hours
            }
        })
        
    except Exception as e:
        logger.error(f"Manual scheduling error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST  
def create_and_schedule_task(request):
    """Create a new task and immediately schedule it to a specific time slot"""
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        estimated_hours = float(data.get('estimated_hours', 1.0))
        priority = int(data.get('priority', 3))
        date_str = data.get('date')  # YYYY-MM-DD
        
        if not title:
            return JsonResponse({
                'success': False,
                'error': 'Task title is required'
            })
        
        # Handle both legacy hour-only format and new time format
        if 'time' in data:
            time_str = data.get('time')  # HH:MM format
            # Parse the date and time
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            start_datetime = timezone.make_aware(
                datetime.combine(date_obj, time_obj)
            )
        else:
            # Legacy format - hour only (for backward compatibility)
            hour = int(data.get('hour'))  # 6-24
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_datetime = timezone.make_aware(
                datetime.combine(date_obj, datetime.min.time().replace(hour=hour))
            )
        end_datetime = start_datetime + timedelta(hours=estimated_hours)
        
        # Check for conflicts
        conflicting_tasks = Task.objects.filter(
            user=request.user,
            start_time__lt=end_datetime,
            end_time__gt=start_datetime
        )
        
        if conflicting_tasks.exists():
            return JsonResponse({
                'success': False,
                'error': f'Time slot conflicts with: {", ".join([t.title for t in conflicting_tasks])}'
            })
        
        # Create and schedule the task
        with transaction.atomic():
            task = Task.objects.create(
                user=request.user,
                title=title,
                description=description,
                estimated_hours=estimated_hours,
                priority=priority,
                start_time=start_datetime,
                end_time=end_datetime,
                deadline=start_datetime + timedelta(days=7)  # Default deadline
            )
            
            # Sync to Google Calendar if enabled
            try:
                service = GoogleCalendarService(request.user)
                # Check if service has Google integration
                from .models import GoogleCalendarIntegration
                integration = GoogleCalendarIntegration.objects.filter(user=request.user).first()
                if integration and integration.is_enabled and service.service:
                    service.sync_task_to_google(task)
            except Exception as e:
                logger.warning(f"Google Calendar sync failed: {e}")
        
        return JsonResponse({
            'success': True,
            'message': f'Task "{task.title}" created and scheduled for {start_datetime.strftime("%B %d at %I:%M %p")}',
            'task': {
                'id': task.id,
                'title': task.title,
                'start_time': start_datetime.isoformat(),
                'end_time': end_datetime.isoformat(),
                'estimated_hours': estimated_hours
            }
        })
        
    except Exception as e:
        logger.error(f"Create and schedule error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
def unschedule_task(request):
    """Remove scheduling from a task (make it unscheduled)"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        
        task = get_object_or_404(Task, id=task_id, user=request.user)
        
        with transaction.atomic():
            # Store Google Calendar event ID before clearing
            google_event_id = getattr(task, 'google_calendar_event_id', None)
            
            task.start_time = None
            task.end_time = None
            task.save()
            
            # Remove from Google Calendar if it was synced
            if google_event_id:
                try:
                    service = GoogleCalendarService(request.user)
                    if service.is_enabled():
                        service.delete_google_event(google_event_id)
                except Exception as e:
                    logger.warning(f"Google Calendar deletion failed: {e}")
        
        return JsonResponse({
            'success': True,
            'message': f'Task "{task.title}" unscheduled'
        })
        
    except Exception as e:
        logger.error(f"Unschedule error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
