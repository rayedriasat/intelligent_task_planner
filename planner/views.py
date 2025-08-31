from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
import json
import logging
# Add these imports at the top
from datetime import datetime, timedelta
from django.db.models import Q
from .models import Task, TimeBlock, PomodoroSession, NotificationPreference
from .forms import TaskForm, QuickTaskForm, TimeBlockForm
from .services.scheduling_engine import SchedulingEngine

# Global request counter for debugging
sync_request_counter = 0

logger = logging.getLogger(__name__)


# Create your views here.


class OnboardingView(LoginRequiredMixin, TemplateView):
    """Quick-start onboarding for new users."""
    template_name = 'planner/onboarding.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = QuickTaskForm()
        return context

    def post(self, request, *args, **kwargs):
        form = QuickTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()

            # Create default availability for new users
            self._create_default_availability(request.user)

            # Try to schedule the task
            engine = SchedulingEngine(request.user)
            scheduled_tasks, unscheduled_tasks = engine.calculate_schedule([task])

            if scheduled_tasks:
                for scheduled_task in scheduled_tasks:
                    scheduled_task.save()
                messages.success(request, f'Great! Your task "{task.title}" has been scheduled. Add more availability to build a complete schedule.')
            else:
                messages.warning(request, f'Task "{task.title}" was created but couldn\'t be scheduled. Please add your availability.')

            return redirect('planner:dashboard')

        return self.render_to_response({'form': form})

    def _create_default_availability(self, user):
        """Create some default availability for new users."""
        now = timezone.now()
        today = now.date()
        
        # Create availability for next 7 days, 9 AM to 5 PM
        for i in range(7):
            day = today + timedelta(days=i)
            start_time = timezone.make_aware(datetime.combine(day, datetime.min.time().replace(hour=9)))
            end_time = timezone.make_aware(datetime.combine(day, datetime.min.time().replace(hour=17)))
            
            TimeBlock.objects.create(
                user=user,
                start_time=start_time,
                end_time=end_time,
                is_recurring=False
            )


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard - redirects to Kanban by default."""
    template_name = 'planner/dashboard.html'

    def get(self, request, *args, **kwargs):
        # Check if user is new (no tasks)
        if not request.user.tasks.exists():
            return redirect('planner:onboarding')
        return redirect('planner:kanban')


class KanbanView(LoginRequiredMixin, TemplateView):
    """Kanban board view for task management."""
    template_name = 'planner/kanban.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_tasks = self.request.user.tasks.all()
        
        context['todo_tasks'] = user_tasks.filter(status='todo')
        context['in_progress_tasks'] = user_tasks.filter(status='in_progress')
        context['completed_tasks'] = user_tasks.filter(status='completed')
        context['task_form'] = TaskForm()
        
        return context


class TaskListView(LoginRequiredMixin, ListView):
    """List view of all user tasks."""
    model = Task
    template_name = 'planner/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


class TaskCreateView(LoginRequiredMixin, CreateView):
    """Create a new task."""
    model = Task
    form_class = TaskForm
    template_name = 'planner/task_form.html'
    success_url = reverse_lazy('planner:kanban')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        # Don't automatically schedule - let users manually schedule or use re-optimize
        messages.success(self.request, f'Task "{self.object.title}" created! Drag it to a time slot or use Re-optimize to schedule it.')
        
        return response


class TaskDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a single task."""
    model = Task
    template_name = 'planner/task_detail.html'

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing task."""
    model = Task
    form_class = TaskForm
    template_name = 'planner/task_form.html'

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('planner:task_detail', kwargs={'pk': self.object.pk})


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a task."""
    model = Task
    template_name = 'planner/task_confirm_delete.html'
    success_url = reverse_lazy('planner:kanban')

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


# Add these to your existing views.py

class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'planner/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get week from URL parameter or default to current week
        week_param = self.request.GET.get('week')
        if week_param:
            try:
                base_date = datetime.strptime(week_param, '%Y-%m-%d').date()
            except ValueError:
                base_date = timezone.now().date()
        else:
            base_date = timezone.now().date()
        
        # Calculate week start (Monday) and end (Sunday)
        week_start = base_date - timedelta(days=base_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Get user's tasks for this week using datetime range instead of date range
        # to avoid MySQL timezone conversion issues
        week_start_dt = timezone.make_aware(datetime.combine(week_start, datetime.min.time()))
        week_end_dt = timezone.make_aware(datetime.combine(week_end, datetime.max.time()))
        
        scheduled_tasks = self.request.user.tasks.filter(
            start_time__gte=week_start_dt,
            start_time__lte=week_end_dt
        ).order_by('start_time')

        unscheduled_tasks = self.request.user.tasks.filter(
            start_time__isnull=True,
            status__in=['todo', 'in_progress']
        ).order_by('deadline')

        # Generate week days with tasks
        week_days = []
        today = timezone.now().date()
        for i in range(7):
            day = week_start + timedelta(days=i)
            # Filter tasks for this day from the already-fetched scheduled_tasks
            # to avoid timezone conversion issues
            day_tasks = []
            for task in scheduled_tasks:
                if task.start_time.date() == day:
                    # Convert UTC time to local timezone for positioning
                    local_start_time = task.start_time
                    if timezone.is_aware(local_start_time):
                        # Convert to the Django configured timezone
                        local_start_time = timezone.localtime(local_start_time)
                    
                    # Calculate task position (6 AM = position 0)
                    task_hour = local_start_time.hour
                    task_minute = local_start_time.minute
                    
                    # Position relative to 6 AM (our first hour) 
                    # Each hour slot is 4rem tall
                    if task_hour >= 6:  # Only show tasks from 6 AM onwards
                        position_hours = task_hour - 6  # Hours since 6 AM
                        position_minutes = task_minute / 60.0  # Convert minutes to decimal hours
                        task_top = (position_hours + position_minutes) * 4  # 4rem per hour
                        
                        # Task height based on estimated hours
                        task_height = float(task.estimated_hours) * 4  # 4rem per hour
                        
                        # Add positioning data to task
                        task.position_top = task_top
                        task.position_height = task_height
                        day_tasks.append(task)
            
            week_days.append({
                'date': day,
                'day_name': day.strftime('%A'),
                'day_short': day.strftime('%a'),
                'day_num': day.day,
                'is_today': day == today,
                'tasks': day_tasks
            })

        # Check Google Calendar integration
        from .models import GoogleCalendarIntegration
        google_integration = GoogleCalendarIntegration.objects.filter(
            user=self.request.user
        ).first()
        
        # Auto-sync disabled - user preference
        # Note: Auto-sync can be re-enabled by uncommenting the code below
        # if (google_integration and google_integration.is_enabled and 
        #     (not google_integration.last_sync or 
        #      timezone.now() - google_integration.last_sync > timedelta(hours=1))):
        #     # Auto-sync code here...
        
        # Calculate navigation dates
        prev_week = week_start - timedelta(days=7)
        next_week = week_start + timedelta(days=7)
        
        # Generate hour range for calendar display (6 AM to 11 PM)
        hours = []
        for hour in range(6, 24):  # 6 AM to 11 PM
            if hour == 0:
                time_label = "12 AM"
            elif hour < 12:
                time_label = f"{hour}:00 AM"
            elif hour == 12:
                time_label = "12 PM"
            else:
                time_label = f"{hour - 12}:00 PM"
            
            hours.append({
                'hour': hour,
                'label': time_label
            })

        context.update({
            'week_start': week_start,
            'week_end': week_end,
            'prev_week': prev_week,
            'next_week': next_week,
            'week_days': week_days,
            'hours': hours,
            'scheduled_tasks': scheduled_tasks,
            'unscheduled_tasks': unscheduled_tasks,
            'google_integration': google_integration,
            'has_google_calendar': google_integration is not None,
        })
        
        return context

@login_required
@require_POST
def update_task_schedule(request):
    """Update task schedule via AJAX."""
    try:
        task_id = request.POST.get('task_id')
        start_time_str = request.POST.get('start_time')
        
        task = get_object_or_404(Task, id=task_id, user=request.user)
        
        # Parse start time
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        
        # Calculate end time
        duration = timedelta(hours=float(task.estimated_hours))
        end_time = start_time + duration
        
        # Update task
        task.start_time = start_time
        task.end_time = end_time
        task.is_locked = True
        task.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def unschedule_task(request):
    """Remove task from schedule."""
    try:
        task_id = request.POST.get('task_id')
        task = get_object_or_404(Task, id=task_id, user=request.user)
        
        task.start_time = None
        task.end_time = None
        task.is_locked = False
        task.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def reoptimize_week(request):
    """Re-optimize the schedule using the enhanced scheduling engine with optimization history tracking."""
    try:
        from .models import OptimizationHistory
        
        # Create snapshot of current state before optimization
        optimization_history = OptimizationHistory(user=request.user)
        current_task_snapshot = optimization_history.create_task_snapshot(request.user)
        
        engine = SchedulingEngine(request.user)
        
        # Use the enhanced scheduling with analysis
        result = engine.calculate_schedule_with_analysis()
        
        # Save optimization history
        optimization_history.previous_task_state = current_task_snapshot
        optimization_history.scheduled_count = len(result['scheduled_tasks'])
        optimization_history.unscheduled_count = len(result['unscheduled_tasks'])
        optimization_history.utilization_rate = result['utilization_rate']
        optimization_history.total_hours_scheduled = result['total_hours_scheduled']
        optimization_history.was_overloaded = result['overload_analysis']['is_overloaded']
        
        if result['overload_analysis']['is_overloaded']:
            optimization_history.overload_ratio = result['overload_analysis']['overload_ratio']
            optimization_history.excess_hours = result['overload_analysis']['excess_hours']
            optimization_history.recommendations = result['overload_analysis']['recommendations']
        
        # Store optimization decisions for transparency
        optimization_history.optimization_decisions = {
            'algorithm_used': 'enhanced_priority_with_splitting',
            'priority_factors': ['deadline_urgency', 'task_priority', 'estimated_hours'],
            'task_splitting_enabled': True,
            'overload_handling': 'priority_based_selection'
        }
        
        optimization_history.save()
        
        # Send optimization notification
        from .services.notification_service import NotificationService
        NotificationService.send_optimization_notification(
            request.user,
            f"Schedule optimization complete! {len(result['scheduled_tasks'])} tasks scheduled with {round(result['utilization_rate'], 1)}% utilization."
        )
        
        # Save scheduled tasks
        with transaction.atomic():
            for task in result['scheduled_tasks']:
                task.save()
        
        # Prepare response with analysis and undo option
        response_data = {
            'success': True,
            'message': f'Schedule optimized! {len(result["scheduled_tasks"])} tasks scheduled.',
            'scheduled_count': len(result['scheduled_tasks']),
            'unscheduled_count': len(result['unscheduled_tasks']),
            'utilization_rate': round(result['utilization_rate'], 1),
            'overload_analysis': result['overload_analysis'],
            'optimization_id': optimization_history.id,
            'can_undo': True,  # Can undo for 1 hour
        }
        
        # Add recommendations if overloaded
        if result['overload_analysis']['is_overloaded']:
            response_data['recommendations'] = result['overload_analysis']['recommendations']
            response_data['message'] += f' Warning: Schedule overloaded by {result["overload_analysis"]["excess_hours"]:.1f} hours.'
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def undo_optimization(request):
    """Undo the last optimization run."""
    try:
        from .models import OptimizationHistory
        
        optimization_id = request.POST.get('optimization_id')
        
        if optimization_id:
            # Undo specific optimization
            optimization = get_object_or_404(
                OptimizationHistory, 
                id=optimization_id, 
                user=request.user
            )
        else:
            # Undo last optimization
            optimization = OptimizationHistory.objects.filter(
                user=request.user
            ).first()
            
            if not optimization:
                return JsonResponse({
                    'success': False, 
                    'error': 'No optimization found to undo'
                })
        
        # Check if undo is allowed (within time limit)
        if not optimization.can_undo:
            return JsonResponse({
                'success': False, 
                'error': 'Optimization too old to undo (1 hour limit)'
            })
        
        # Restore previous task state
        success = optimization.restore_task_state()
        
        if success:
            return JsonResponse({
                'success': True,
                'message': f'Optimization from {optimization.timestamp.strftime("%H:%M")} has been undone',
                'restored_tasks': len(optimization.previous_task_state)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to restore previous state'
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



class AvailabilityView(LoginRequiredMixin, TemplateView):
    """Manage user's time availability."""
    template_name = 'planner/availability.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_blocks'] = self.request.user.time_blocks.all().order_by('start_time')
        context['form'] = TimeBlockForm()
        return context


class TimeBlockCreateView(LoginRequiredMixin, CreateView):
    """Create a new time block."""
    model = TimeBlock
    form_class = TimeBlockForm
    template_name = 'planner/timeblock_form.html'
    success_url = reverse_lazy('planner:availability')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TimeBlockDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a time block."""
    model = TimeBlock
    template_name = 'planner/timeblock_confirm_delete.html'
    success_url = reverse_lazy('planner:availability')

    def get_queryset(self):
        return TimeBlock.objects.filter(user=self.request.user)


class PomodoroTimerView(LoginRequiredMixin, TemplateView):
    """Pomodoro timer interface."""
    template_name = 'pomodoro.html'
    
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

# HTMX and API Views

@login_required
@require_POST
def update_task_status(request):
    """Update task status via HTMX or AJAX."""
    task_id = request.POST.get('task_id')
    new_status = request.POST.get('status')
    
    if not task_id or not new_status:
        return JsonResponse({'error': 'Missing required fields'}, status=400)
    
    try:
        task = get_object_or_404(Task, id=task_id, user=request.user)
        task.status = new_status
        
        # If marked as completed, log completion time
        if new_status == 'completed' and not task.actual_hours:
            if task.is_scheduled:
                task.actual_hours = task.duration_hours
        
        task.save()
        
        return JsonResponse({'success': True, 'status': new_status})
    
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def toggle_task_status(request, pk):
    """Toggle task status between todo/in_progress/completed."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    status_cycle = {'todo': 'in_progress', 'in_progress': 'completed', 'completed': 'todo'}
    task.status = status_cycle.get(task.status, 'todo')
    task.save()
    
    return render(request, 'planner/partials/task_card.html', {'task': task})


@login_required
@require_POST
def toggle_task_lock(request, pk):
    """Toggle task lock status."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.is_locked = not task.is_locked
    task.save()
    
    return render(request, 'planner/partials/task_card.html', {'task': task})


@login_required
@require_POST
def reoptimize_schedule(request):
    """Re-optimize the user's schedule."""
    engine = SchedulingEngine(request.user)
    scheduled_tasks, unscheduled_tasks = engine.reschedule_week()
    
    # Save scheduled tasks
    with transaction.atomic():
        for task in scheduled_tasks:
            task.save()
    
    messages.success(request, f'Schedule optimized! {len(scheduled_tasks)} tasks scheduled.')
    
    # Return updated calendar view
    return redirect('planner:calendar')


@login_required
@require_POST
def update_task_time(request):
    """Update task time via drag and drop."""
    task_id = request.POST.get('task_id')
    start_time_str = request.POST.get('start_time')
    end_time_str = request.POST.get('end_time')
    
    if not all([task_id, start_time_str, end_time_str]):
        return JsonResponse({'error': 'Missing required fields'}, status=400)
    
    try:
        task = get_object_or_404(Task, id=task_id, user=request.user)
        
        # Parse datetime strings
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        
        # Update task
        task.start_time = start_time
        task.end_time = end_time
        task.is_locked = True  # Auto-lock manually moved tasks
        task.save()
        
        return JsonResponse({'success': True})
    
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid datetime format'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def task_card_partial(request, pk):
    """Return a single task card partial."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    return render(request, 'planner/partials/task_card.html', {'task': task})


@login_required
def unscheduled_tasks_partial(request):
    """Return unscheduled tasks partial."""
    tasks = request.user.tasks.filter(
        status__in=['todo', 'in_progress'],
        start_time__isnull=True
    )
    return render(request, 'planner/partials/unscheduled_tasks.html', {'tasks': tasks})


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


@login_required
@require_POST
def quick_schedule_task(request):
    """Quick schedule a single task in the next available slot."""
    try:
        task_id = request.POST.get('task_id')
        task = get_object_or_404(Task, id=task_id, user=request.user)
        
        engine = SchedulingEngine(request.user)
        
        # Try to schedule just this one task
        scheduled_tasks, unscheduled_tasks = engine.calculate_schedule([task])
        
        if scheduled_tasks:
            scheduled_task = scheduled_tasks[0]
            scheduled_task.save()
            
            return JsonResponse({
                'success': True,
                'scheduled_time': scheduled_task.start_time.strftime('%b %d at %I:%M %p'),
                'task_title': scheduled_task.title
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No available time slots found for this task'
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def schedule_urgent_tasks(request):
    """Schedule all urgent tasks automatically."""
    try:
        # Get urgent tasks (due within 2 days)
        urgent_deadline = timezone.now() + timedelta(days=2)
        
        urgent_tasks = list(request.user.tasks.filter(
            deadline__lte=urgent_deadline,
            start_time__isnull=True,
            status__in=['todo', 'in_progress']
        ).order_by('deadline', 'priority'))
        
        if not urgent_tasks:
            return JsonResponse({
                'success': True,
                'scheduled_count': 0,
                'message': 'No urgent tasks found'
            })
        
        engine = SchedulingEngine(request.user)
        scheduled_tasks, unscheduled_tasks = engine.calculate_schedule(urgent_tasks)
        
        # Save scheduled tasks
        with transaction.atomic():
            for task in scheduled_tasks:
                task.save()
        
        return JsonResponse({
            'success': True,
            'scheduled_count': len(scheduled_tasks),
            'unscheduled_count': len(unscheduled_tasks),
            'message': f'Scheduled {len(scheduled_tasks)} urgent tasks'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def create_urgent_task(request):
    """Create an urgent task and check if sacrifice mode is needed."""
    try:
        from .forms import TaskForm
        
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.priority = 1  # Force high priority for urgent tasks
            task.save()
            
            # Check if there's available time for this task
            engine = SchedulingEngine(request.user)
            available_slots = engine._generate_available_slots(list(request.user.time_blocks.all()))
            
            # Calculate total available time
            total_available = sum(engine._slot_duration(slot) for slot in available_slots)
            required_time = float(task.estimated_hours)
            
            if total_available >= required_time:
                # Try to schedule normally
                scheduled_slot = engine._find_suitable_slot(task, available_slots)
                if scheduled_slot:
                    task.start_time = scheduled_slot['start']
                    task.end_time = scheduled_slot['end']
                    task.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Urgent task scheduled successfully',
                        'task_id': task.id,
                        'scheduled': True
                    })
            
            # No available time - trigger sacrifice mode
            conflicting_tasks = request.user.tasks.filter(
                start_time__isnull=False,
                end_time__isnull=False,
                status__in=['todo', 'in_progress'],
                is_locked=False
            ).order_by('start_time')
            
            return JsonResponse({
                'success': True,
                'message': 'No available time slots. Choose tasks to reschedule.',
                'task_id': task.id,
                'scheduled': False,
                'sacrifice_mode': True,
                'conflicting_tasks': [
                    {
                        'id': t.id,
                        'title': t.title,
                        'start_time': t.start_time.isoformat(),
                        'end_time': t.end_time.isoformat(),
                        'estimated_hours': float(t.estimated_hours),
                        'priority': t.priority,
                        'is_locked': t.is_locked
                    } for t in conflicting_tasks
                ]
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid form data',
                'errors': form.errors
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def sacrifice_tasks(request):
    """Execute sacrifice mode - bump selected tasks to make room for urgent task."""
    try:
        urgent_task_id = request.POST.get('urgent_task_id')
        sacrifice_task_ids = request.POST.getlist('sacrifice_task_ids')
        target_datetime = request.POST.get('target_datetime')
        
        if not urgent_task_id or not target_datetime:
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters'
            })
        
        urgent_task = get_object_or_404(Task, id=urgent_task_id, user=request.user)
        target_time = datetime.fromisoformat(target_datetime.replace('Z', '+00:00'))
        if timezone.is_naive(target_time):
            target_time = timezone.make_aware(target_time)
        
        with transaction.atomic():
            # Unschedule sacrifice tasks
            if sacrifice_task_ids:
                sacrifice_tasks_qs = Task.objects.filter(
                    id__in=sacrifice_task_ids,
                    user=request.user,
                    is_locked=False
                )
                
                for task in sacrifice_tasks_qs:
                    task.start_time = None
                    task.end_time = None
                    task.save()
            
            # Schedule the urgent task
            duration = timedelta(hours=float(urgent_task.estimated_hours))
            urgent_task.start_time = target_time
            urgent_task.end_time = target_time + duration
            urgent_task.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Urgent task scheduled. {len(sacrifice_task_ids)} tasks moved to unscheduled.',
            'sacrificed_count': len(sacrifice_task_ids)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


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
        from .models import NotificationPreference
        return NotificationPreference.get_or_create_for_user(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Notification preferences updated successfully!')
        return super().form_valid(form)


@login_required
def get_notifications(request):
    """API endpoint to get pending notifications for the current user."""
    try:
        from .models import TaskNotification
        
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
        from .models import TaskNotification
        
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
        from .services.notification_service import NotificationService
        
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


@login_required
def get_ai_scheduling_suggestions(request):
    """API endpoint to get AI-powered scheduling suggestions."""
    try:
        from .services.ai_service import get_ai_scheduling_suggestions_sync
        
        # Get unscheduled tasks
        unscheduled_tasks = list(request.user.tasks.filter(
            start_time__isnull=True,
            status__in=['todo', 'in_progress']
        ))
        
        if not unscheduled_tasks:
            return JsonResponse({
                'success': False,
                'error': 'No unscheduled tasks found',
                'suggestions': []
            })
        
        # Get available time blocks (next 7 days)
        from datetime import timedelta
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        
        # Find time blocks that overlap with the next 7 days
        # A block overlaps if: block.start_time < end_date AND block.end_time > start_date
        available_blocks = list(request.user.time_blocks.filter(
            start_time__lt=end_date,  # Block starts before the 7-day window ends
            end_time__gt=start_date   # Block ends after the window starts
        ))
        
        if not available_blocks:
            return JsonResponse({
                'success': False,
                'error': 'No available time blocks found for the next 7 days',
                'suggestions': []
            })
        
        # Call AI service
        ai_response = get_ai_scheduling_suggestions_sync(unscheduled_tasks, available_blocks)
        
        if ai_response.success:
            # Format suggestions for frontend
            suggestions_data = []
            for suggestion in ai_response.suggestions:
                # Get task details
                try:
                    task = next(t for t in unscheduled_tasks if t.id == suggestion.task_id)
                    suggestions_data.append({
                        'task_id': suggestion.task_id,
                        'task_title': task.title,
                        'task_description': task.description,
                        'suggested_start_time': suggestion.suggested_start_time,
                        'suggested_end_time': suggestion.suggested_end_time,
                        'confidence_score': suggestion.confidence_score,
                        'reasoning': suggestion.reasoning
                    })
                except StopIteration:
                    continue  # Task not found, skip
            
            return JsonResponse({
                'success': True,
                'suggestions': suggestions_data,
                'overall_score': ai_response.overall_score,
                'reasoning': ai_response.reasoning,
                'total_tasks_analyzed': len(unscheduled_tasks),
                'total_suggestions': len(suggestions_data)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': ai_response.error_message,
                'reasoning': ai_response.reasoning,
                'suggestions': []
            })
            
    except Exception as e:
        logger.error(f"Error in get_ai_scheduling_suggestions: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Service error: {str(e)}',
            'suggestions': []
        })


@login_required
@require_POST
def apply_ai_suggestions(request):
    """Apply selected AI scheduling suggestions to actually schedule tasks."""
    try:
        selected_suggestions = request.POST.getlist('selected_suggestions')
        
        if not selected_suggestions:
            return JsonResponse({
                'success': False,
                'error': 'No suggestions selected'
            })
        
        # Get fresh AI suggestions to ensure data integrity
        from .services.ai_service import get_ai_scheduling_suggestions_sync
        
        # Get unscheduled tasks
        unscheduled_tasks = list(request.user.tasks.filter(
            start_time__isnull=True,
            status__in=['todo', 'in_progress']
        ))
        
        # Get available time blocks
        from datetime import timedelta
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        
        # Find time blocks that overlap with the next 7 days
        available_blocks = list(request.user.time_blocks.filter(
            start_time__lt=end_date,  # Block starts before the 7-day window ends
            end_time__gt=start_date   # Block ends after the window starts
        ))
        
        # Get fresh AI suggestions
        ai_response = get_ai_scheduling_suggestions_sync(unscheduled_tasks, available_blocks)
        
        if not ai_response.success:
            return JsonResponse({
                'success': False,
                'error': 'Unable to retrieve current AI suggestions'
            })
        
        # Apply selected suggestions
        applied_count = 0
        
        with transaction.atomic():
            for suggestion in ai_response.suggestions:
                # Check if this suggestion was selected
                suggestion_id = f"{suggestion.task_id}_{suggestion.suggested_start_time}"
                if suggestion_id in selected_suggestions:
                    try:
                        # Get the task
                        task = request.user.tasks.get(id=suggestion.task_id)
                        
                        # Parse suggested times
                        start_time = timezone.datetime.fromisoformat(suggestion.suggested_start_time.replace('Z', '+00:00'))
                        end_time = timezone.datetime.fromisoformat(suggestion.suggested_end_time.replace('Z', '+00:00'))
                        
                        # Apply the scheduling
                        task.start_time = start_time
                        task.end_time = end_time
                        task.save()
                        
                        applied_count += 1
                        
                    except (Task.DoesNotExist, ValueError) as e:
                        logger.warning(f"Failed to apply suggestion for task {suggestion.task_id}: {e}")
                        continue
        
        # Send notification about applied AI suggestions
        from .services.notification_service import NotificationService
        NotificationService.send_optimization_notification(
            request.user,
            f"AI suggestions applied! {applied_count} tasks have been scheduled based on AI recommendations."
        )
        
        return JsonResponse({
            'success': True,
            'applied_count': applied_count,
            'message': f'Successfully applied {applied_count} AI suggestions'
        })
        
    except Exception as e:
        logger.error(f"Error applying AI suggestions: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to apply suggestions: {str(e)}'
        })


# Google Calendar Integration Views

class GoogleCalendarSettingsView(LoginRequiredMixin, TemplateView):
    """View for managing Google Calendar integration settings."""
    template_name = 'planner/google_calendar_settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from .models import GoogleCalendarIntegration, CalendarSyncLog
            integration = GoogleCalendarIntegration.objects.get(user=self.request.user)
        except:
            integration = None
        
        # Get recent sync logs
        try:
            from .models import CalendarSyncLog
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
            from .models import GoogleCalendarIntegration
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
    
    from .models import SyncLock
    
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
        from .services.google_calendar_service import GoogleCalendarService
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
    from .models import SyncLock
    
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
        
        from .services.google_calendar_service import GoogleCalendarService
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
    from .models import SyncLock
    
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
        from .services.google_calendar_service import GoogleCalendarService
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
        from .models import GoogleCalendarIntegration, CalendarSyncLog
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
        from .models import GoogleCalendarIntegration
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
            from .models import GoogleCalendarIntegration
            integration = GoogleCalendarIntegration.objects.get(user=self.request.user)
        except:
            integration = None
        
        context.update({
            'integration': integration,
        })
        
        return context
