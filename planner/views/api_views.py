from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from ..models import Task

logger = logging.getLogger(__name__)


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
