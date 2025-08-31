"""
Views for Google Calendar integration.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, timedelta
import json

from ..models import Task, GoogleCalendarIntegration, CalendarSyncLog
from ..services.google_calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)


class GoogleCalendarSettingsView(LoginRequiredMixin, TemplateView):
    """View for managing Google Calendar integration settings."""
    template_name = 'planner/google_calendar_settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            integration = GoogleCalendarIntegration.objects.get(user=self.request.user)
        except GoogleCalendarIntegration.DoesNotExist:
            integration = None
        
        # Get recent sync logs
        sync_logs = CalendarSyncLog.objects.filter(
            user=self.request.user
        )[:10]
        
        context.update({
            'integration': integration,
            'sync_logs': sync_logs,
            'has_google_token': self._has_google_token(),
        })
        
        return context
    
    def _has_google_token(self):
        """Check if user has valid Google OAuth token."""
        from allauth.socialaccount.models import SocialToken
        return SocialToken.objects.filter(
            account__user=self.request.user,
            account__provider='google'
        ).exists()
    
    def post(self, request, *args, **kwargs):
        """Handle settings updates."""
        try:
            integration, created = GoogleCalendarIntegration.objects.get_or_create(
                user=request.user
            )
            
            # Update settings
            integration.is_enabled = request.POST.get('is_enabled') == 'on'
            integration.sync_direction = request.POST.get('sync_direction', 'both')
            integration.save()
            
            messages.success(request, 'Google Calendar settings updated successfully!')
            
        except Exception as e:
            logger.error(f"Error updating Google Calendar settings: {e}")
            messages.error(request, 'Failed to update settings. Please try again.')
        
        return redirect('planner:google_calendar_settings')


@login_required
@require_POST
def sync_to_google(request):
    """Sync tasks to Google Calendar."""
    try:
        service = GoogleCalendarService(request.user)
        result = service.sync_tasks_to_google()
        
        if result['success']:
            message = f"Sync completed! Created {result['events_created']} events, updated {result['events_updated']} events."
            if result['errors']:
                message += f" {len(result['errors'])} errors occurred."
            
            return JsonResponse({
                'success': True,
                'message': message,
                'events_created': result['events_created'],
                'events_updated': result['events_updated'],
                'errors': result['errors']
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Sync failed. Please check your Google Calendar connection.'
            })
            
    except Exception as e:
        logger.error(f"Error syncing to Google Calendar: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Sync failed: {str(e)}'
        })


@login_required
@require_POST
def sync_from_google(request):
    """Sync events from Google Calendar."""
    try:
        # Get date range from request
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
            start_date = timezone.make_aware(start_date)
        else:
            start_date = timezone.now()
        
        if end_date:
            end_date = datetime.fromisoformat(end_date)
            end_date = timezone.make_aware(end_date)
        else:
            end_date = start_date + timedelta(days=30)
        
        service = GoogleCalendarService(request.user)
        result = service.sync_from_google(start_date, end_date)
        
        if result['success']:
            message = f"Sync completed! Imported {result['events_created']} events, updated {result['events_updated']} tasks."
            if result['errors']:
                message += f" {len(result['errors'])} errors occurred."
            
            return JsonResponse({
                'success': True,
                'message': message,
                'events_created': result['events_created'],
                'events_updated': result['events_updated'],
                'errors': result['errors']
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Sync failed. Please check your Google Calendar connection.'
            })
            
    except Exception as e:
        logger.error(f"Error syncing from Google Calendar: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Sync failed: {str(e)}'
        })


@login_required
@require_POST
def full_sync(request):
    """Perform a full two-way sync."""
    try:
        service = GoogleCalendarService(request.user)
        
        # First sync tasks to Google
        to_google_result = service.sync_tasks_to_google()
        
        # Then sync from Google
        from_google_result = service.sync_from_google()
        
        if to_google_result['success'] and from_google_result['success']:
            message = (
                f"Full sync completed! "
                f"To Google: {to_google_result['events_created']} created, {to_google_result['events_updated']} updated. "
                f"From Google: {from_google_result['events_created']} imported, {from_google_result['events_updated']} updated."
            )
            
            total_errors = to_google_result['errors'] + from_google_result['errors']
            if total_errors:
                message += f" {len(total_errors)} errors occurred."
            
            return JsonResponse({
                'success': True,
                'message': message,
                'to_google': to_google_result,
                'from_google': from_google_result,
                'errors': total_errors
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Full sync partially failed. Please check sync logs.'
            })
            
    except Exception as e:
        logger.error(f"Error performing full sync: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Full sync failed: {str(e)}'
        })


@login_required
def sync_status(request):
    """Get sync status and recent logs."""
    try:
        integration = GoogleCalendarIntegration.objects.filter(user=request.user).first()
        recent_logs = CalendarSyncLog.objects.filter(user=request.user)[:5]
        
        logs_data = []
        for log in recent_logs:
            logs_data.append({
                'id': log.id,
                'sync_type': log.get_sync_type_display(),
                'status': log.status,
                'timestamp': log.timestamp.isoformat(),
                'events_synced': log.events_synced,
                'error_message': log.error_message,
                'duration': str(log.sync_duration) if log.sync_duration else None
            })
        
        return JsonResponse({
            'success': True,
            'integration': {
                'is_enabled': integration.is_enabled if integration else False,
                'last_sync': integration.last_sync.isoformat() if integration and integration.last_sync else None,
                'sync_direction': integration.sync_direction if integration else 'both'
            },
            'recent_logs': logs_data
        })
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to get sync status: {str(e)}'
        })


@login_required
@require_POST
def toggle_auto_sync(request):
    """Enable/disable automatic syncing."""
    try:
        integration, created = GoogleCalendarIntegration.objects.get_or_create(
            user=request.user
        )
        
        integration.is_enabled = not integration.is_enabled
        integration.save()
        
        return JsonResponse({
            'success': True,
            'is_enabled': integration.is_enabled,
            'message': f"Auto-sync {'enabled' if integration.is_enabled else 'disabled'}"
        })
        
    except Exception as e:
        logger.error(f"Error toggling auto-sync: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to toggle auto-sync: {str(e)}'
        })
