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
        
        # Calculate urgent tasks (due within 2 days)
        urgent_deadline = timezone.now() + timedelta(days=2)
        urgent_tasks_count = user_tasks.filter(
            deadline__lte=urgent_deadline,
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
        queryset = Task.objects.filter(user=self.request.user)
        
        # Get filter parameters from GET request
        search = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        priority = self.request.GET.get('priority', '')
        
        # Apply search filter (search in title and description)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        # Apply status filter
        if status:
            queryset = queryset.filter(status=status)
        
        # Apply priority filter
        if priority:
            try:
                priority_int = int(priority)
                queryset = queryset.filter(priority=priority_int)
            except (ValueError, TypeError):
                pass  # Ignore invalid priority values
        
        # Default ordering by priority (highest first) then by deadline
        return queryset.order_by('-priority', 'deadline')


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


@login_required
@require_POST
def bulk_delete_tasks(request):
    """Delete multiple tasks at once."""
    try:
        task_ids = request.POST.getlist('task_ids[]')
        if not task_ids:
            return JsonResponse({'success': False, 'error': 'No tasks selected'})
        
        # Convert to integers and filter by user
        task_ids = [int(id) for id in task_ids]
        deleted_count = Task.objects.filter(
            id__in=task_ids,
            user=request.user
        ).delete()[0]
        
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'{deleted_count} task(s) deleted successfully'
        })
        
    except (ValueError, TypeError) as e:
        return JsonResponse({'success': False, 'error': 'Invalid task IDs'})
    except Exception as e:
        logger.error(f'Error bulk deleting tasks: {e}')
        return JsonResponse({'success': False, 'error': 'Failed to delete tasks'})


@login_required
@require_POST
def delete_completed_tasks(request):
    """Delete all completed tasks for the user."""
    try:
        deleted_count = Task.objects.filter(
            user=request.user,
            status='completed'
        ).delete()[0]
        
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'{deleted_count} completed task(s) deleted successfully'
        })
        
    except Exception as e:
        logger.error(f'Error deleting completed tasks: {e}')
        return JsonResponse({'success': False, 'error': 'Failed to delete completed tasks'})


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view showing email and connected accounts."""
    template_name = 'planner/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get Google account information
        from allauth.socialaccount.models import SocialAccount
        google_account = SocialAccount.objects.filter(
            user=self.request.user, 
            provider='google'
        ).first()
        
        # Get Google Calendar integration
        from ..models import GoogleCalendarIntegration
        try:
            google_integration = GoogleCalendarIntegration.objects.get(
                user=self.request.user
            )
        except GoogleCalendarIntegration.DoesNotExist:
            google_integration = None
        
        # Get Canvas integration
        from ..models import CanvasIntegration
        try:
            canvas_integration = CanvasIntegration.objects.get(
                user=self.request.user
            )
        except CanvasIntegration.DoesNotExist:
            canvas_integration = None
        
        # Get task completion stats for consistency report
        current_year = timezone.now().year
                
        # Calculate total tasks completed this year
        year_start = timezone.make_aware(datetime(current_year, 1, 1))
        year_end = timezone.make_aware(datetime(current_year, 12, 31, 23, 59, 59))
                
        completed_this_year = Task.objects.filter(
            user=self.request.user,
            status='completed',
            updated_at__gte=year_start,
            updated_at__lte=year_end
        ).count()
                
        # Get current streak (consecutive days with completed tasks)
        today = timezone.now().date()
        current_streak = 0
        check_date = today
                
        while True:
            day_completed = Task.objects.filter(
                user=self.request.user,
                status='completed',
                updated_at__date=check_date
            ).exists()
                    
            if day_completed:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break
                        
            # Limit to reasonable streak length
            if current_streak > 365:
                break
                
        # Calculate completion rate for this month
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
                
        completed_this_month = Task.objects.filter(
            user=self.request.user,
            status='completed',
            updated_at__gte=month_start,
            updated_at__lt=next_month
        ).count()
                
        total_tasks_this_month = Task.objects.filter(
            user=self.request.user,
            created_at__gte=month_start,
            created_at__lt=next_month
        ).count()
                
        completion_rate = (completed_this_month / total_tasks_this_month * 100) if total_tasks_this_month > 0 else 0
        
        context.update({
            'google_account': google_account,
            'google_integration': google_integration,
            'canvas_integration': canvas_integration,
            'consistency_stats': {
                'completed_this_year': completed_this_year,
                'current_streak': current_streak,
                'completion_rate': round(completion_rate, 1),
                'current_year': current_year
            }
        })
        
        return context
    success_url = reverse_lazy('planner:kanban')

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)
