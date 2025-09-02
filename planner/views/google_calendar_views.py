from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Global request counter for debugging
sync_request_counter = 0


class GoogleCalendarSettingsView(LoginRequiredMixin, TemplateView):
    """View for managing Google Calendar integration settings."""
    template_name = 'planner/google_calendar_settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from ..models import GoogleCalendarIntegration, CalendarSyncLog
            integration = GoogleCalendarIntegration.objects.get(user=self.request.user)
        except:
            integration = None
        
        # Get recent sync logs
        try:
            from ..models import CalendarSyncLog
            sync_logs = CalendarSyncLog.objects.filter(
                user=self.request.user
            )[:10]
        except:
            sync_logs = []
        
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
            from ..models import GoogleCalendarIntegration
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
    global sync_request_counter
    sync_request_counter += 1
    current_count = sync_request_counter
    
    # Get request ID from headers (if sent by client)
    request_id = request.META.get('HTTP_X_REQUEST_ID', f'server-{current_count}')
    
    # COMPLETELY BLOCK AUTO-SYNC - Only allow manual sync
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    referer = request.META.get('HTTP_REFERER', '')
    request_method = request.method
    request_path = request.get_full_path()
    
    logger.info(f"SYNC DEBUG: sync_to_google called #{current_count} (Request ID: {request_id}) for user {request.user.id} from IP {request.META.get('REMOTE_ADDR')}")
    logger.info(f"SYNC DEBUG: Method: {request_method}, Path: {request_path}")
    logger.info(f"SYNC DEBUG: User-Agent: {user_agent[:100]}...")
    logger.info(f"SYNC DEBUG: Referer: {referer}")
    logger.info(f"SYNC DEBUG: POST data: {dict(request.POST)}")
    logger.info(f"SYNC DEBUG: Headers: {dict(request.headers)}")
    
    from ..models import SyncLock
    
    # Try to acquire sync lock with longer timeout to prevent browser retries
    lock_acquired, lock_instance = SyncLock.acquire_lock(request.user, timeout_minutes=10)
    if not lock_acquired:
        logger.warning(f"SYNC DEBUG: sync_to_google #{current_count} (Request ID: {request_id}) BLOCKED - lock already exists for user {request.user.id}")
        return JsonResponse({
            'success': False,
            'message': 'Another sync operation is already in progress. Please wait for it to complete.',
            'request_id': request_id
        })
    
    logger.info(f"SYNC DEBUG: sync_to_google #{current_count} (Request ID: {request_id}) PROCEEDING for user {request.user.id}")
    try:
        from ..services.google_calendar_service import GoogleCalendarService
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
    finally:
        # Always release the sync lock
        logger.info(f"SYNC DEBUG: sync_to_google #{current_count} (Request ID: {request_id}) FINISHED - releasing lock for user {request.user.id}")
        SyncLock.release_lock(request.user)


@login_required
@require_POST
def sync_from_google(request):
    """Sync events from Google Calendar."""
    from ..models import SyncLock
    
    # Try to acquire sync lock
    lock_acquired, lock_instance = SyncLock.acquire_lock(request.user, timeout_minutes=5)
    if not lock_acquired:
        return JsonResponse({
            'success': False,
            'message': 'Another sync operation is already in progress. Please wait for it to complete.'
        })
    
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
        
        from ..services.google_calendar_service import GoogleCalendarService
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
    finally:
        # Always release the sync lock
        SyncLock.release_lock(request.user)


@login_required
@require_POST
def full_sync(request):
    """Perform a full two-way sync."""
    global sync_request_counter
    sync_request_counter += 1
    current_count = sync_request_counter
    
    logger.info(f"SYNC DEBUG: full_sync called #{current_count} for user {request.user.id} from IP {request.META.get('REMOTE_ADDR')}")
    from ..models import SyncLock
    
    # Try to acquire sync lock with longer timeout for full sync
    lock_acquired, lock_instance = SyncLock.acquire_lock(request.user, timeout_minutes=10)
    if not lock_acquired:
        logger.warning(f"SYNC DEBUG: full_sync #{current_count} BLOCKED - lock already exists for user {request.user.id}")
        return JsonResponse({
            'success': False,
            'message': 'Another sync operation is already in progress. Please wait for it to complete.'
        })
    
    logger.info(f"SYNC DEBUG: full_sync #{current_count} PROCEEDING for user {request.user.id}")
    try:
        from ..services.google_calendar_service import GoogleCalendarService
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
    finally:
        # Always release the sync lock
        logger.info(f"SYNC DEBUG: full_sync #{current_count} FINISHED - releasing lock for user {request.user.id}")
        SyncLock.release_lock(request.user)


@login_required
def sync_status(request):
    """Get sync status and recent logs."""
    try:
        from ..models import GoogleCalendarIntegration, CalendarSyncLog
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
        from ..models import GoogleCalendarIntegration
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


class GoogleConnectionView(LoginRequiredMixin, TemplateView):
    """View for managing Google account connection and troubleshooting."""
    template_name = 'planner/google_connection.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from ..models import GoogleCalendarIntegration
            integration = GoogleCalendarIntegration.objects.get(user=self.request.user)
        except:
            integration = None
        
        context.update({
            'integration': integration,
        })
        
        return context
