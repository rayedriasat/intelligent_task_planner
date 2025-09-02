from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from ..models import Task, PomodoroSession

logger = logging.getLogger(__name__)


class PomodoroTimerView(LoginRequiredMixin, TemplateView):
    """Pomodoro timer interface."""
    template_name = 'pomodoro.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Check subscription before allowing access."""
        from billing.services import user_has_pomodoro_access
        from django.shortcuts import redirect
        from django.contrib import messages
        from django.urls import reverse
        
        if not user_has_pomodoro_access(request.user):
            messages.warning(
                request, 
                'You need a Pomodoro subscription to access this feature.'
            )
            return redirect(reverse('billing:subscribe') + '?feature=pomodoro')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's active/in-progress tasks for the timer
        available_tasks = self.request.user.tasks.filter(
            status__in=['todo', 'in_progress']
        ).order_by('deadline')
        
        # Get current active session if any
        active_session = PomodoroSession.objects.filter(
            task__user=self.request.user,
            status='active'
        ).first()
        
        # Get recent sessions for history
        recent_sessions = PomodoroSession.objects.filter(
            task__user=self.request.user
        ).select_related('task')[:10]
        
        # Calculate today's stats
        today = timezone.now().date()
        today_sessions = PomodoroSession.objects.filter(
            task__user=self.request.user,
            start_time__date=today,
            status='completed'
        )
        
        context.update({
            'available_tasks': available_tasks,
            'active_session': active_session,
            'recent_sessions': recent_sessions,
            'today_focus_time': sum(s.actual_duration or 0 for s in today_sessions),
            'today_sessions_count': today_sessions.count(),
        })
        
        return context


@login_required
@require_POST
def start_pomodoro_session(request):
    """Start a new Pomodoro session."""
    from billing.services import user_has_pomodoro_access
    
    if not user_has_pomodoro_access(request.user):
        return JsonResponse({
            'success': False,
            'error': 'You need a Pomodoro subscription to access this feature.',
            'redirect_url': '/billing/subscribe/?feature=pomodoro'
        }, status=403)
    try:
        task_id = request.POST.get('task_id')
        session_type = request.POST.get('session_type', 'focus')
        
        if not task_id:
            return JsonResponse({'error': 'Task ID is required'}, status=400)
        
        task = get_object_or_404(Task, id=task_id, user=request.user)
        
        # Check if there's already an active session
        active_session = PomodoroSession.objects.filter(
            task__user=request.user,
            status='active'
        ).first()
        
        if active_session:
            return JsonResponse({'error': 'You already have an active session'}, status=400)
        
        # Set duration based on session type
        duration_map = {
            'focus': 25,
            'short_break': 5,
            'long_break': 15
        }
        
        # Create new session
        session = PomodoroSession.objects.create(
            task=task,
            session_type=session_type,
            planned_duration=duration_map.get(session_type, 25)
        )
        
        # Update task status to in_progress if it's not already
        if task.status == 'todo':
            task.status = 'in_progress'
            task.save()
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'duration': session.planned_duration,
            'message': f'Started {session.get_session_type_display().lower()} for {task.title}'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def complete_pomodoro_session(request):
    """Complete the current Pomodoro session."""
    from billing.services import user_has_pomodoro_access
    
    if not user_has_pomodoro_access(request.user):
        return JsonResponse({
            'success': False,
            'error': 'You need a Pomodoro subscription to access this feature.',
            'redirect_url': '/billing/subscribe/?feature=pomodoro'
        }, status=403)
    try:
        session_id = request.POST.get('session_id')
        actual_minutes = request.POST.get('actual_minutes')
        notes = request.POST.get('notes', '')
        
        session = get_object_or_404(
            PomodoroSession, 
            id=session_id, 
            task__user=request.user,
            status='active'
        )
        
        # Complete the session
        session.status = 'completed'
        session.end_time = timezone.now()
        session.actual_duration = int(actual_minutes) if actual_minutes else session.planned_duration
        session.notes = notes
        session.save()
        
        # Update task's actual hours
        if session.session_type == 'focus':
            task = session.task
            if task.actual_hours:
                task.actual_hours = float(task.actual_hours) + (session.actual_duration / 60.0)
            else:
                task.actual_hours = session.actual_duration / 60.0
            task.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Session completed! You focused for {session.actual_duration} minutes.',
            'next_suggestion': get_next_session_suggestion(session)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def pause_pomodoro_session(request):
    """Pause the current Pomodoro session."""
    from billing.services import user_has_pomodoro_access
    
    if not user_has_pomodoro_access(request.user):
        return JsonResponse({
            'success': False,
            'error': 'You need a Pomodoro subscription to access this feature.',
            'redirect_url': '/billing/subscribe/?feature=pomodoro'
        }, status=403)
    try:
        session_id = request.POST.get('session_id')
        
        session = get_object_or_404(
            PomodoroSession, 
            id=session_id, 
            task__user=request.user,
            status='active'
        )
        
        session.status = 'paused'
        session.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Session paused'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def cancel_pomodoro_session(request):
    """Cancel the current Pomodoro session."""
    from billing.services import user_has_pomodoro_access
    
    if not user_has_pomodoro_access(request.user):
        return JsonResponse({
            'success': False,
            'error': 'You need a Pomodoro subscription to access this feature.',
            'redirect_url': '/billing/subscribe/?feature=pomodoro'
        }, status=403)
    try:
        session_id = request.POST.get('session_id')
        
        session = get_object_or_404(
            PomodoroSession, 
            id=session_id, 
            task__user=request.user,
            status__in=['active', 'paused']
        )
        
        session.status = 'cancelled'
        session.end_time = timezone.now()
        session.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Session cancelled'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_next_session_suggestion(completed_session):
    """Suggest what type of session to do next."""
    user = completed_session.task.user
    
    # Count focus sessions today
    today = timezone.now().date()
    today_focus_sessions = PomodoroSession.objects.filter(
        task__user=user,
        start_time__date=today,
        session_type='focus',
        status='completed'
    ).count()
    
    if completed_session.session_type == 'focus':
        # After 4 focus sessions, suggest long break
        if today_focus_sessions % 4 == 0:
            return {'type': 'long_break', 'duration': 15, 'message': 'Time for a longer break!'}
        else:
            return {'type': 'short_break', 'duration': 5, 'message': 'Take a short break!'}
    else:
        # After any break, suggest focus session
        return {'type': 'focus', 'duration': 25, 'message': 'Ready to focus again?'}


# Legacy Pomodoro functions for backward compatibility

@login_required
@require_POST
def start_pomodoro(request):
    """Start a Pomodoro session."""
    task_id = request.POST.get('task_id')
    
    if not task_id:
        return JsonResponse({'error': 'Task ID required'}, status=400)
    
    try:
        task = get_object_or_404(Task, id=task_id, user=request.user)
        
        # Update task to in_progress if not already
        if task.status == 'todo':
            task.status = 'in_progress'
            task.save()
        
        return JsonResponse({
            'success': True,
            'task_title': task.title,
            'duration': 25  # 25 minutes
        })
    
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)


@login_required
@require_POST
def complete_pomodoro(request):
    """Complete a Pomodoro session."""
    task_id = request.POST.get('task_id')
    
    if not task_id:
        return JsonResponse({'error': 'Task ID required'}, status=400)
    
    try:
        task = get_object_or_404(Task, id=task_id, user=request.user)
        
        # Create Pomodoro session record
        now = timezone.now()
        start_time = now - timedelta(minutes=25)
        
        PomodoroSession.objects.create(
            task=task,
            start_time=start_time,
            end_time=now
        )
        
        return JsonResponse({'success': True})
    
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)
