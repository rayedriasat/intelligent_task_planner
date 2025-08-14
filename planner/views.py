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
from datetime import datetime, timedelta

from .models import Task, TimeBlock, PomodoroSession
from .forms import TaskForm, QuickTaskForm, TimeBlockForm
from .services.scheduling_engine import SchedulingEngine


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
        
        # Try to schedule the new task
        engine = SchedulingEngine(self.request.user)
        scheduled_tasks, unscheduled_tasks = engine.calculate_schedule([self.object])
        
        if scheduled_tasks:
            for task in scheduled_tasks:
                task.save()
            messages.success(self.request, f'Task "{self.object.title}" created and scheduled!')
        else:
            messages.info(self.request, f'Task "{self.object.title}" created but needs more availability to be scheduled.')
        
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


class CalendarView(LoginRequiredMixin, TemplateView):
    """Weekly calendar view showing scheduled tasks."""
    template_name = 'planner/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's tasks and time blocks
        tasks = self.request.user.tasks.filter(status__in=['todo', 'in_progress'])
        time_blocks = self.request.user.time_blocks.all()
        
        # Get scheduled and unscheduled tasks
        engine = SchedulingEngine(self.request.user)
        scheduled_tasks, unscheduled_tasks = engine.calculate_schedule(list(tasks), list(time_blocks))
        
        context['scheduled_tasks'] = scheduled_tasks
        context['unscheduled_tasks'] = unscheduled_tasks
        context['time_blocks'] = time_blocks
        
        # Generate week days for calendar
        now = timezone.now()
        week_start = now - timedelta(days=now.weekday())
        context['week_days'] = []
        
        for i in range(7):
            day = week_start + timedelta(days=i)
            context['week_days'].append({
                'date': day,
                'day_name': day.strftime('%A'),
                'day_short': day.strftime('%a'),
                'day_num': day.day
            })
        
        return context


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


class PomodoroView(LoginRequiredMixin, TemplateView):
    """Pomodoro timer interface."""
    template_name = 'planner/pomodoro.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['in_progress_tasks'] = self.request.user.tasks.filter(status='in_progress')
        return context


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
