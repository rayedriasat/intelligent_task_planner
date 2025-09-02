from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CanvasSettingsView(LoginRequiredMixin, TemplateView):
    """View for managing Canvas LMS integration settings."""
    template_name = 'planner/canvas_settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from ..models import CanvasIntegration, CanvasSyncLog
            integration = CanvasIntegration.objects.get(user=self.request.user)
        except CanvasIntegration.DoesNotExist:
            integration = None
        
        # Get recent sync logs
        try:
            from ..models import CanvasSyncLog
            sync_logs = CanvasSyncLog.objects.filter(
                user=self.request.user
            )[:10]
        except:
            sync_logs = []
        
        context.update({
            'integration': integration,
            'sync_logs': sync_logs,
            'is_configured': integration.is_configured if integration else False,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle settings updates."""
        try:
            from ..models import CanvasIntegration
            integration, created = CanvasIntegration.objects.get_or_create(
                user=request.user
            )
            
            # Update settings
            integration.canvas_base_url = request.POST.get('canvas_base_url', '').strip()
            integration.canvas_access_token = request.POST.get('canvas_access_token', '').strip()
            integration.is_enabled = request.POST.get('is_enabled') == 'on'
            integration.sync_assignments = request.POST.get('sync_assignments') == 'on'
            integration.sync_todos = request.POST.get('sync_todos') == 'on'
            integration.sync_announcements = request.POST.get('sync_announcements') == 'on'
            integration.save()
            
            # Test connection if credentials provided
            if integration.is_configured:
                from ..services.canvas_service import CanvasService
                try:
                    service = CanvasService(request.user)
                    test_result = service.test_connection()
                    if test_result['success']:
                        messages.success(request, f'Canvas integration configured successfully! {test_result["message"]}')
                    else:
                        messages.warning(request, f'Canvas settings saved but connection test failed: {test_result["message"]}')
                except Exception as e:
                    messages.warning(request, f'Canvas settings saved but connection test failed: {str(e)}')
            else:
                messages.success(request, 'Canvas settings saved!')
            
        except Exception as e:
            logger.error(f"Error updating Canvas settings: {e}")
            messages.error(request, 'Failed to update settings. Please try again.')
        
        return redirect('planner:canvas_settings')


@login_required
def canvas_connection_status(request):
    """Check Canvas connection status via AJAX."""
    try:
        from ..models import CanvasIntegration
        integration = CanvasIntegration.objects.filter(user=request.user).first()
        
        if not integration or not integration.is_configured:
            return JsonResponse({
                'success': False,
                'message': 'Canvas integration not configured'
            })
        
        from ..services.canvas_service import CanvasService
        service = CanvasService(request.user)
        result = service.test_connection()
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error checking Canvas connection: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Connection test failed: {str(e)}'
        })


@login_required
@require_POST
def sync_canvas_assignments(request):
    """Sync assignments from Canvas LMS."""
    try:
        from ..services.canvas_service import CanvasService
        service = CanvasService(request.user)
        result = service.sync_assignments()
        
        if result['success']:
            message = (
                f"Assignment sync completed! "
                f"Synced {result['assignments_synced']} assignments, "
                f"created {result['tasks_created']} new tasks, "
                f"updated {result['tasks_updated']} existing tasks."
            )
            if result['errors']:
                message += f" {len(result['errors'])} errors occurred."
            
            return JsonResponse({
                'success': True,
                'message': message,
                **result
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Assignment sync failed. Please check your Canvas configuration.'
            })
            
    except Exception as e:
        logger.error(f"Error syncing Canvas assignments: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Assignment sync failed: {str(e)}'
        })


@login_required
@require_POST
def sync_canvas_todos(request):
    """Sync todo items from Canvas LMS."""
    try:
        from ..services.canvas_service import CanvasService
        service = CanvasService(request.user)
        result = service.sync_todos()
        
        if result['success']:
            message = (
                f"Todo sync completed! "
                f"Synced {result['todos_synced']} items, "
                f"created {result['tasks_created']} new tasks, "
                f"updated {result['tasks_updated']} existing tasks."
            )
            if result['errors']:
                message += f" {len(result['errors'])} errors occurred."
            
            return JsonResponse({
                'success': True,
                'message': message,
                **result
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Todo sync failed. Please check your Canvas configuration.'
            })
            
    except Exception as e:
        logger.error(f"Error syncing Canvas todos: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Todo sync failed: {str(e)}'
        })


@login_required
@require_POST
def sync_canvas_announcements(request):
    """Sync announcements from Canvas LMS."""
    try:
        from ..services.canvas_service import CanvasService
        service = CanvasService(request.user)
        result = service.sync_announcements()
        
        if result['success']:
            message = f"Announcement sync completed! Synced {result['announcements_synced']} announcements."
            if result['errors']:
                message += f" {len(result['errors'])} errors occurred."
            
            return JsonResponse({
                'success': True,
                'message': message,
                **result
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Announcement sync failed. Please check your Canvas configuration.'
            })
            
    except Exception as e:
        logger.error(f"Error syncing Canvas announcements: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Announcement sync failed: {str(e)}'
        })


@login_required
@require_POST
def sync_canvas_full(request):
    """Perform full Canvas sync (assignments, todos, and announcements)."""
    try:
        from ..services.canvas_service import CanvasService
        service = CanvasService(request.user)
        results = service.full_sync()
        
        if results['overall_success']:
            message_parts = []
            
            if results['assignments'].get('success'):
                assignments = results['assignments']
                message_parts.append(
                    f"Assignments: {assignments['assignments_synced']} synced, "
                    f"{assignments['tasks_created']} tasks created, "
                    f"{assignments['tasks_updated']} tasks updated"
                )
            
            if results['todos'].get('success'):
                todos = results['todos']
                message_parts.append(
                    f"Todos: {todos['todos_synced']} synced, "
                    f"{todos['tasks_created']} tasks created, "
                    f"{todos['tasks_updated']} tasks updated"
                )
            
            if results['announcements'].get('success'):
                announcements = results['announcements']
                message_parts.append(f"Announcements: {announcements['announcements_synced']} synced")
            
            message = "Full Canvas sync completed! " + "; ".join(message_parts)
            
            # Count total errors
            total_errors = []
            for result in [results['assignments'], results['todos'], results['announcements']]:
                if isinstance(result, dict) and result.get('errors'):
                    total_errors.extend(result['errors'])
            
            if total_errors:
                message += f" {len(total_errors)} errors occurred."
            
            return JsonResponse({
                'success': True,
                'message': message,
                'results': results,
                'errors': total_errors
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Full Canvas sync partially failed. Please check sync logs.',
                'results': results
            })
            
    except Exception as e:
        logger.error(f"Error performing full Canvas sync: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Full Canvas sync failed: {str(e)}'
        })


@login_required
def canvas_sync_status(request):
    """Get Canvas sync status and recent logs."""
    try:
        from ..models import CanvasIntegration, CanvasSyncLog
        integration = CanvasIntegration.objects.filter(user=request.user).first()
        recent_logs = CanvasSyncLog.objects.filter(user=request.user)[:5]
        
        logs_data = []
        for log in recent_logs:
            logs_data.append({
                'id': log.id,
                'sync_type': log.get_sync_type_display(),
                'status': log.status,
                'timestamp': log.timestamp.isoformat(),
                'assignments_synced': log.assignments_synced,
                'todos_synced': log.todos_synced,
                'announcements_synced': log.announcements_synced,
                'tasks_created': log.tasks_created,
                'tasks_updated': log.tasks_updated,
                'error_message': log.error_message,
                'duration': str(log.sync_duration) if log.sync_duration else None
            })
        
        return JsonResponse({
            'success': True,
            'integration': {
                'is_enabled': integration.is_enabled if integration else False,
                'is_configured': integration.is_configured if integration else False,
                'last_sync': integration.last_sync.isoformat() if integration and integration.last_sync else None,
                'sync_assignments': integration.sync_assignments if integration else True,
                'sync_todos': integration.sync_todos if integration else True,
                'sync_announcements': integration.sync_announcements if integration else True,
            },
            'recent_logs': logs_data
        })
        
    except Exception as e:
        logger.error(f"Error getting Canvas sync status: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to get sync status: {str(e)}'
        })


@login_required
@require_POST
def toggle_canvas_integration(request):
    """Enable/disable Canvas integration."""
    try:
        from ..models import CanvasIntegration
        integration, created = CanvasIntegration.objects.get_or_create(
            user=request.user
        )
        
        integration.is_enabled = not integration.is_enabled
        integration.save()
        
        return JsonResponse({
            'success': True,
            'is_enabled': integration.is_enabled,
            'message': f"Canvas integration {'enabled' if integration.is_enabled else 'disabled'}"
        })
        
    except Exception as e:
        logger.error(f"Error toggling Canvas integration: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to toggle integration: {str(e)}'
        })


class CanvasDataView(LoginRequiredMixin, TemplateView):
    """View for browsing synced Canvas data."""
    template_name = 'planner/canvas_data.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from ..models import CanvasAssignment, CanvasTodo, CanvasAnnouncement
            
            # Get recent Canvas data
            assignments = CanvasAssignment.objects.filter(user=self.request.user)[:20]
            todos = CanvasTodo.objects.filter(user=self.request.user)[:20]
            announcements = CanvasAnnouncement.objects.filter(
                user=self.request.user,
                posted_at__gte=timezone.now() - timedelta(days=30)
            )[:20]
            
            context.update({
                'assignments': assignments,
                'todos': todos,
                'announcements': announcements,
            })
            
        except Exception as e:
            logger.error(f"Error loading Canvas data: {e}")
            context.update({
                'assignments': [],
                'todos': [],
                'announcements': [],
            })
        
        return context


@login_required
@require_http_methods(["GET", "POST"])
def canvas_announcement_to_task(request, announcement_id):
    """Convert a Canvas announcement to a task."""
    if request.method == 'GET':
        # Return announcement data for the form
        try:
            from ..models import CanvasAnnouncement
            announcement = get_object_or_404(CanvasAnnouncement, id=announcement_id, user=request.user)
            
            return JsonResponse({
                'success': True,
                'announcement': {
                    'id': announcement.id,
                    'title': announcement.title,
                    'message': announcement.message,
                    'course_name': announcement.course_name,
                    'posted_at': announcement.posted_at.isoformat(),
                    'html_url': announcement.html_url,
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting announcement data: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Failed to get announcement: {str(e)}'
            })
    
    elif request.method == 'POST':
        # Create task from announcement
        try:
            from ..models import CanvasAnnouncement, Task
            announcement = get_object_or_404(CanvasAnnouncement, id=announcement_id, user=request.user)
            
            if announcement.task:
                return JsonResponse({
                    'success': False,
                    'message': 'Task already exists for this announcement'
                })
            
            # Get form data
            title = request.POST.get('title', f"[{announcement.course_name}] {announcement.title}")
            description = request.POST.get('description', announcement.message)
            deadline = request.POST.get('deadline')
            priority = int(request.POST.get('priority', 2))
            estimated_hours = float(request.POST.get('estimated_hours', 1.0))
            
            # Parse deadline
            if deadline:
                deadline = timezone.make_aware(datetime.fromisoformat(deadline))
            else:
                deadline = timezone.now() + timedelta(days=7)
            
            # Create task
            task = Task.objects.create(
                user=request.user,
                title=title,
                description=description,
                deadline=deadline,
                priority=priority,
                estimated_hours=estimated_hours,
                source='canvas',
                external_id=announcement.canvas_id,
                status='todo'
            )
            
            # Link announcement to task
            announcement.task = task
            announcement.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Task created from announcement successfully!',
                'task_id': task.id,
                'task_url': reverse('planner:task_detail', kwargs={'pk': task.id})
            })
            
        except Exception as e:
            logger.error(f"Error creating task from announcement: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Failed to create task: {str(e)}'
            })
