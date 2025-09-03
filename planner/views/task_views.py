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
from datetime import datetime, timedelta
from django.db.models import Q

from ..models import Task, TimeBlock, PomodoroSession, NotificationPreference
from ..forms import TaskForm, QuickTaskForm, TimeBlockForm
from ..services.scheduling_engine import SchedulingEngine

logger = logging.getLogger(__name__)


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
            
            # Check if task should be marked as urgent based on deadline
            if task.deadline:
                time_until_deadline = task.deadline - timezone.now()
                if time_until_deadline <= timedelta(hours=24) and time_until_deadline > timedelta(0):
                    task.priority = 4  # Set to urgent
                else:
                    task.priority = 2  # Default to medium
            else:
                task.priority = 2  # Default to medium
            
            task.save()

            # Create default availability for new users
            self._create_default_availability(request.user)

            # Try to schedule the task
            engine = SchedulingEngine(request.user)
            scheduled_tasks, unscheduled_tasks = engine.calculate_schedule([task])

            if scheduled_tasks:
                for scheduled_task in scheduled_tasks:
                    scheduled_task.save()
                if task.priority == 4:
                    messages.success(request, f'Great! Your URGENT task "{task.title}" has been scheduled. Add more availability to build a complete schedule.')
                else:
                    messages.success(request, f'Great! Your task "{task.title}" has been scheduled. Add more availability to build a complete schedule.')
            else:
                if task.priority == 4:
                    messages.warning(request, f'URGENT task "{task.title}" was created but couldn\'t be scheduled. Please add your availability.')
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
    """Main dashboard with overview statistics."""
    template_name = 'planner/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's tasks and calculate stats
        user_tasks = self.request.user.tasks.all()
        today = timezone.now().date()
        
        # Calculate task status counts
        total_tasks = user_tasks.count()
        completed_tasks_count = user_tasks.filter(status='completed').count()
        in_progress_tasks_count = user_tasks.filter(status='in_progress').count()
        todo_tasks_count = user_tasks.filter(status='todo').count()
        
        # Calculate urgent tasks (due within 24 hours or marked as urgent priority)
        urgent_deadline = timezone.now() + timedelta(hours=24)
        urgent_tasks_count = user_tasks.filter(
            Q(deadline__lte=urgent_deadline, deadline__gt=timezone.now()) | Q(priority=4),
            status__in=['todo', 'in_progress']
        ).count()
        
        # Recent tasks (last 10 updated)
        recent_tasks = user_tasks.order_by('-updated_at')[:10]
        
        # Schedule overview stats
        scheduled_tasks_count = user_tasks.filter(start_time__isnull=False).count()
        unscheduled_tasks_count = user_tasks.filter(start_time__isnull=True, status__in=['todo', 'in_progress']).count()
        
        context.update({
            'total_tasks': total_tasks,
            'completed_tasks_count': completed_tasks_count,
            'in_progress_tasks_count': in_progress_tasks_count,
            'todo_tasks_count': todo_tasks_count,
            'recent_tasks': recent_tasks,
            'urgent_tasks_count': urgent_tasks_count,
            'scheduled_tasks_count': scheduled_tasks_count,
            'unscheduled_tasks_count': unscheduled_tasks_count,
        })
        
        return context

    def get(self, request, *args, **kwargs):
        # Check if user is new (no tasks)
        if not request.user.tasks.exists():
            return redirect('planner:onboarding')
        
        # Render dashboard instead of redirecting to kanban
        return self.render_to_response(self.get_context_data())


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
        
        # Check if task should be marked as urgent based on deadline
        if form.instance.deadline:
            time_until_deadline = form.instance.deadline - timezone.now()
            if time_until_deadline <= timedelta(hours=24) and time_until_deadline > timedelta(0):
                form.instance.priority = 4  # Set to urgent
        
        response = super().form_valid(form)
        
        # Don't automatically schedule - let users manually schedule or use re-optimize
        if form.instance.priority == 4:
            messages.success(self.request, f'Task "{self.object.title}" created as URGENT (due within 24h)! Drag it to a time slot or use Re-optimize to schedule it.')
        else:
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

    def form_valid(self, form):
        # Check if task should be marked as urgent based on deadline
        if form.instance.deadline:
            time_until_deadline = form.instance.deadline - timezone.now()
            if time_until_deadline <= timedelta(hours=24) and time_until_deadline > timedelta(0):
                form.instance.priority = 4  # Set to urgent
        
        response = super().form_valid(form)
        
        if form.instance.priority == 4:
            messages.success(self.request, f'Task "{self.object.title}" updated as URGENT (due within 24h)!')
        else:
            messages.success(self.request, f'Task "{self.object.title}" updated successfully!')
        
        return response

    def get_success_url(self):
        return reverse('planner:task_detail', kwargs={'pk': self.object.pk})


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a task."""
    model = Task
    template_name = 'planner/task_confirm_delete.html'
    success_url = reverse_lazy('planner:kanban')

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)
