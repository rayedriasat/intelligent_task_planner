from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
import logging
from datetime import datetime, timedelta

from ..models import Task
from ..services.scheduling_engine import SchedulingEngine

logger = logging.getLogger(__name__)


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
        from ..models import OptimizationHistory
        
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
        optimization_history.total_hours_scheduled = result['total_scheduled_hours']
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
        from ..services.notification_service import NotificationService
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
        from ..models import OptimizationHistory
        
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
def auto_schedule_all_tasks(request):
    """Automatically schedule all tasks with proper rearrangement for urgent tasks."""
    try:
        # Get ALL tasks that need scheduling (including already scheduled non-locked tasks)
        # This allows for proper rearrangement when urgent tasks are added
        all_tasks = request.user.tasks.filter(
            status__in=['todo', 'in_progress'],
            is_locked=False  # Don't move locked tasks
        )
        
        # Get purely unscheduled tasks for the message
        unscheduled_tasks = request.user.tasks.filter(
            start_time__isnull=True,
            status__in=['todo', 'in_progress']
        )
        
        if not all_tasks.exists():
            return JsonResponse({
                'success': True,
                'message': 'No tasks to schedule',
                'scheduled_count': 0
            })
        
        # Clear existing schedule for non-locked tasks to allow proper rearrangement
        # Use the built-in reschedule_week method which handles this properly
        engine = SchedulingEngine(request.user)
        scheduled_tasks, unscheduled_tasks = engine.reschedule_week()
        
        scheduled_count = len(scheduled_tasks)
        final_unscheduled_count = len(unscheduled_tasks)
        
        # Save scheduled tasks to database
        with transaction.atomic():
            for task in scheduled_tasks:
                task.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Re-arranged schedule: {scheduled_count} tasks scheduled with proper priority order',
            'scheduled_count': scheduled_count,
            'unscheduled_count': final_unscheduled_count,
            'utilization_rate': 0,  # TODO: Calculate utilization if needed
            'recommendations': []  # TODO: Add recommendations if needed
        })
        
    except Exception as e:
        logger.error(f"Auto-scheduling error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


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
            
            # Ensure we're working with the user's timezone
            local_time = scheduled_task.start_time
            if hasattr(local_time, 'astimezone'):
                # Convert to local timezone if it's timezone-aware
                from django.utils import timezone as tz
                local_time = local_time.astimezone(tz.get_current_timezone())
            
            # Use the same time format as calendar blocks: "g:i A" (e.g., "1:11 PM")
            # Django's "g:i A" format: hour without leading zero, minutes with leading zero, AM/PM
            hour = local_time.strftime('%I').lstrip('0')  # Remove leading zero from hour
            minute = local_time.strftime('%M')             # Keep leading zero for minutes
            ampm = local_time.strftime('%p')               # AM/PM
            formatted_time = f"{hour}:{minute} {ampm}"
            
            return JsonResponse({
                'success': True,
                'scheduled_time': formatted_time,
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
        # Get urgent tasks (due within 24 hours or priority 4)
        urgent_deadline = timezone.now() + timedelta(hours=24)
        
        urgent_tasks = list(request.user.tasks.filter(
            Q(deadline__lte=urgent_deadline, deadline__gt=timezone.now()) | Q(priority=4),
            start_time__isnull=True,
            status__in=['todo', 'in_progress']
        ).order_by('deadline', '-priority'))  # Sort by deadline first, then by priority (urgent first)
        
        if not urgent_tasks:
            return JsonResponse({
                'success': True,
                'scheduled_count': 0,
                'message': 'No urgent tasks found'
            })
        
        engine = SchedulingEngine(request.user)
        scheduled_tasks, unscheduled_tasks = engine.schedule_urgent_tasks(urgent_tasks)
        
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
        from ..forms import TaskForm
        
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.priority = 1  # Force high priority for urgent tasks
            task.save()
            
            # Check if there's available time for this task
            engine = SchedulingEngine(request.user)
            
            # Try to schedule using the consistent scheduling method
            scheduled_tasks, unscheduled_tasks = engine.calculate_schedule([task])
            
            if scheduled_tasks:
                # Task was successfully scheduled
                scheduled_task = scheduled_tasks[0]
                scheduled_task.save()
                
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
