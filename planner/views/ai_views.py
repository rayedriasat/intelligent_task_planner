from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import logging

from ..models import Task

logger = logging.getLogger(__name__)


@login_required
def get_ai_scheduling_suggestions(request):
    """API endpoint to get AI-powered scheduling suggestions."""
    try:
        from ..services.ai_service import get_ai_scheduling_suggestions_sync
        
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
        logger.info(f"DEBUG: Received selected_suggestions: {selected_suggestions}")
        
        if not selected_suggestions:
            logger.warning("DEBUG: No suggestions selected")
            return JsonResponse({
                'success': False,
                'error': 'No suggestions selected'
            })
        
        # Get fresh AI suggestions to ensure data integrity
        from ..services.ai_service import get_ai_scheduling_suggestions_sync
        
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
            logger.error(f"DEBUG: Failed to get fresh AI suggestions: {ai_response.error_message}")
            return JsonResponse({
                'success': False,
                'error': 'Unable to retrieve current AI suggestions'
            })
            
        logger.info(f"DEBUG: Got {len(ai_response.suggestions)} fresh AI suggestions")
        
        # Apply selected suggestions
        applied_count = 0
        
        with transaction.atomic():
            for suggestion in ai_response.suggestions:
                # Check if this suggestion was selected
                suggestion_id = f"{suggestion.task_id}_{suggestion.suggested_start_time}"
                logger.info(f"DEBUG: Checking suggestion ID: {suggestion_id}")
                logger.info(f"DEBUG: Selected suggestions: {selected_suggestions}")
                
                if suggestion_id in selected_suggestions:
                    logger.info(f"DEBUG: Processing suggestion for task {suggestion.task_id}")
                    try:
                        # Get the task
                        task = request.user.tasks.get(id=suggestion.task_id)
                        logger.info(f"DEBUG: Found task: {task.title}")
                        
                        # Parse suggested times
                        start_time = timezone.datetime.fromisoformat(suggestion.suggested_start_time.replace('Z', '+00:00'))
                        end_time = timezone.datetime.fromisoformat(suggestion.suggested_end_time.replace('Z', '+00:00'))
                        logger.info(f"DEBUG: Parsed times - start: {start_time}, end: {end_time}")
                        
                        # Check for conflicts before applying
                        from ..services.scheduling_engine import SchedulingEngine
                        engine = SchedulingEngine(request.user)
                        
                        if engine._check_for_conflicts(start_time, end_time, exclude_task_id=task.id):
                            logger.warning(f"DEBUG: Conflict detected for task {task.title}, skipping this suggestion")
                            continue
                        
                        # Apply the scheduling
                        task.start_time = start_time
                        task.end_time = end_time
                        task.save()
                        logger.info(f"DEBUG: Successfully scheduled task {task.title}")
                        
                        applied_count += 1
                        
                    except (Task.DoesNotExist, ValueError) as e:
                        logger.warning(f"Failed to apply suggestion for task {suggestion.task_id}: {e}")
                        continue
                else:
                    logger.info(f"DEBUG: Suggestion {suggestion_id} not in selected suggestions")
        
        # Send notification about applied AI suggestions
        from ..services.notification_service import NotificationService
        NotificationService.send_optimization_notification(
            request.user,
            f"AI suggestions applied! {applied_count} tasks have been scheduled based on AI recommendations."
        )
        
        logger.info(f"DEBUG: Successfully applied {applied_count} AI suggestions")
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


class AIChatView(LoginRequiredMixin, TemplateView):
    """AI Chat interface for scheduling assistance."""
    template_name = 'planner/ai_chat.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Check subscription before allowing access."""
        from billing.services import user_has_ai_chat_access
        from django.shortcuts import redirect
        from django.contrib import messages
        from django.urls import reverse
        
        if not user_has_ai_chat_access(request.user):
            messages.warning(
                request, 
                'You need an AI Chat subscription to access this feature.'
            )
            return redirect(reverse('billing:subscribe') + '?feature=ai_chat')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's task and schedule context for AI
        user_tasks = self.request.user.tasks.all().order_by('deadline')
        time_blocks = self.request.user.time_blocks.all().order_by('start_time')
        
        # Recent optimization history
        recent_optimizations = []
        if hasattr(self.request.user, 'optimization_history'):
            from ..models import OptimizationHistory
            recent_optimizations = OptimizationHistory.objects.filter(
                user=self.request.user
            ).order_by('-timestamp')[:5]
        
        # Calculate some stats for context
        total_tasks = user_tasks.count()
        completed_tasks = user_tasks.filter(status='completed').count()
        scheduled_tasks = user_tasks.filter(start_time__isnull=False).count()
        unscheduled_tasks = total_tasks - scheduled_tasks
        
        # Recent activity summary
        today = timezone.now().date()
        tasks_due_today = user_tasks.filter(
            deadline__date=today,
            status__in=['todo', 'in_progress']
        ).count()
        
        tasks_due_soon = user_tasks.filter(
            deadline__date__lte=today + timedelta(days=3),
            deadline__date__gt=today,
            status__in=['todo', 'in_progress']
        ).count()
        
        context.update({
            'user_tasks': user_tasks[:10],  # Recent tasks for display
            'time_blocks': time_blocks,
            'recent_optimizations': recent_optimizations,
            'stats': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'scheduled_tasks': scheduled_tasks,
                'unscheduled_tasks': unscheduled_tasks,
                'tasks_due_today': tasks_due_today,
                'tasks_due_soon': tasks_due_soon,
                'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            }
        })
        
        return context


@login_required
@require_POST
def send_ai_chat_message(request):
    """Send a chat message to AI and get response with full schedule context."""
    from billing.services import user_has_ai_chat_access
    
    if not user_has_ai_chat_access(request.user):
        return JsonResponse({
            'success': False,
            'error': 'You need an AI Chat subscription to access this feature.',
            'redirect_url': '/billing/subscribe/?feature=ai_chat'
        }, status=403)
    try:
        user_message = request.POST.get('message', '').strip()
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            })
        
        # Get comprehensive user context
        user_context = _get_user_schedule_context(request.user)
        
        # Import AI service
        from ..services.ai_service import get_ai_chat_response_sync
        
        # Get AI response with full context
        ai_response = get_ai_chat_response_sync(user_message, user_context)
        
        if ai_response.success:
            # Execute task operations if any
            task_results = []
            if hasattr(ai_response, 'task_operations') and ai_response.task_operations:
                task_results = _execute_task_operations(ai_response.task_operations, request.user)
            
            return JsonResponse({
                'success': True,
                'response': ai_response.response,
                'suggestions': ai_response.suggestions if hasattr(ai_response, 'suggestions') else [],
                'context_used': ai_response.context_summary if hasattr(ai_response, 'context_summary') else None,
                'task_operations': task_results
            })
        else:
            return JsonResponse({
                'success': False,
                'error': ai_response.error_message,
                'fallback_response': 'I apologize, but I\'m having trouble connecting to the AI service right now. Please try again later.'
            })
            
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Chat service error: {str(e)}',
            'fallback_response': 'I apologize, but I\'m experiencing technical difficulties. Please try again later.'
        })


def _execute_task_operations(task_operations, user):
    """Execute task operations requested by AI."""
    from django.utils.dateparse import parse_datetime
    from decimal import Decimal
    
    results = []
    
    for operation in task_operations:
        result = {
            'operation_type': operation.operation_type,
            'success': False,
            'error_message': None,
            'task_id': None,
            'message': ''
        }
        
        try:
            if operation.operation_type == 'create':
                # Create new task
                task_data = {
                    'user': user,
                    'title': operation.title or 'New Task',
                    'status': 'todo'
                }
                
                # Add optional fields if provided
                if operation.description:
                    task_data['description'] = operation.description
                
                if operation.deadline:
                    deadline_dt = parse_datetime(operation.deadline)
                    if deadline_dt:
                        task_data['deadline'] = deadline_dt
                    else:
                        # Default to tomorrow if parsing fails
                        from datetime import timedelta
                        task_data['deadline'] = timezone.now() + timedelta(days=1)
                else:
                    # Default deadline tomorrow
                    from datetime import timedelta
                    task_data['deadline'] = timezone.now() + timedelta(days=1)
                
                if operation.estimated_hours:
                    task_data['estimated_hours'] = Decimal(str(operation.estimated_hours))
                else:
                    task_data['estimated_hours'] = Decimal('1.0')
                
                if operation.priority:
                    task_data['priority'] = operation.priority
                else:
                    task_data['priority'] = 2  # Default medium priority
                
                # Create the task
                task = Task.objects.create(**task_data)
                
                # Schedule the task if start/end times provided
                if operation.start_time and operation.end_time:
                    start_dt = parse_datetime(operation.start_time)
                    end_dt = parse_datetime(operation.end_time)
                    if start_dt and end_dt:
                        task.start_time = start_dt
                        task.end_time = end_dt
                        task.save()
                
                result['success'] = True
                result['task_id'] = task.id
                result['message'] = f"Created task '{task.title}' successfully"
                
            elif operation.operation_type == 'update':
                # Update existing task
                if not operation.task_id:
                    result['error_message'] = 'Task ID required for update operation'
                else:
                    try:
                        task = Task.objects.get(id=operation.task_id, user=user)
                        
                        # Update fields if provided
                        if operation.title:
                            task.title = operation.title
                        if operation.description is not None:
                            task.description = operation.description
                        if operation.deadline:
                            deadline_dt = parse_datetime(operation.deadline)
                            if deadline_dt:
                                task.deadline = deadline_dt
                        if operation.estimated_hours:
                            task.estimated_hours = Decimal(str(operation.estimated_hours))
                        if operation.priority:
                            task.priority = operation.priority
                        if operation.status:
                            task.status = operation.status
                        
                        task.save()
                        result['success'] = True
                        result['task_id'] = task.id
                        result['message'] = f"Updated task '{task.title}' successfully"
                        
                    except Task.DoesNotExist:
                        result['error_message'] = f'Task with ID {operation.task_id} not found'
                        
            elif operation.operation_type == 'complete':
                # Mark task as completed
                if not operation.task_id:
                    result['error_message'] = 'Task ID required for complete operation'
                else:
                    try:
                        task = Task.objects.get(id=operation.task_id, user=user)
                        task.status = 'completed'
                        task.save()
                        
                        result['success'] = True
                        result['task_id'] = task.id
                        result['message'] = f"Marked task '{task.title}' as completed"
                        
                    except Task.DoesNotExist:
                        result['error_message'] = f'Task with ID {operation.task_id} not found'
                        
            elif operation.operation_type == 'schedule':
                # Schedule an existing task
                if not operation.task_id or not operation.start_time or not operation.end_time:
                    result['error_message'] = 'Task ID, start time, and end time required for schedule operation'
                else:
                    try:
                        task = Task.objects.get(id=operation.task_id, user=user)
                        
                        start_dt = parse_datetime(operation.start_time)
                        end_dt = parse_datetime(operation.end_time)
                        
                        if start_dt and end_dt:
                            task.start_time = start_dt
                            task.end_time = end_dt
                            task.save()
                            
                            result['success'] = True
                            result['task_id'] = task.id
                            result['message'] = f"Scheduled task '{task.title}' from {start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%H:%M')}"
                        else:
                            result['error_message'] = 'Invalid start or end time format'
                            
                    except Task.DoesNotExist:
                        result['error_message'] = f'Task with ID {operation.task_id} not found'
                        
            elif operation.operation_type == 'delete':
                # Delete a task
                if not operation.task_id:
                    result['error_message'] = 'Task ID required for delete operation'
                else:
                    try:
                        task = Task.objects.get(id=operation.task_id, user=user)
                        task_title = task.title
                        task.delete()
                        
                        result['success'] = True
                        result['message'] = f"Deleted task '{task_title}' successfully"
                        
                    except Task.DoesNotExist:
                        result['error_message'] = f'Task with ID {operation.task_id} not found'
                        
            else:
                result['error_message'] = f'Unknown operation type: {operation.operation_type}'
                
        except Exception as e:
            logger.error(f"Error executing task operation {operation.operation_type}: {e}")
            result['error_message'] = f'Error executing operation: {str(e)}'
        
        results.append(result)
    
    return results


def _get_user_schedule_context(user):
    """Get comprehensive user context for AI chat."""
    from datetime import datetime, timedelta
    
    # Get tasks
    all_tasks = list(user.tasks.all().order_by('deadline'))
    scheduled_tasks = [t for t in all_tasks if t.is_scheduled]
    unscheduled_tasks = [t for t in all_tasks if not t.is_scheduled]
    
    # Get time blocks
    time_blocks = list(user.time_blocks.all().order_by('start_time'))
    
    # Get recent optimization history
    recent_optimizations = []
    try:
        from ..models import OptimizationHistory
        recent_optimizations = list(OptimizationHistory.objects.filter(
            user=user
        ).order_by('-timestamp')[:3])
    except:
        pass
    
    # Calculate schedule metrics
    today = timezone.now().date()
    now = timezone.now()
    
    # Tasks due today and soon
    tasks_due_today = [t for t in all_tasks if t.deadline.date() == today and t.status != 'completed']
    tasks_due_this_week = [t for t in all_tasks if t.deadline.date() <= today + timedelta(days=7) and t.status != 'completed']
    overdue_tasks = [t for t in all_tasks if t.deadline < now and t.status != 'completed']
    
    # Recent Pomodoro sessions
    recent_pomodoros = []
    try:
        from ..models import PomodoroSession
        recent_pomodoros = list(PomodoroSession.objects.filter(
            task__user=user,
            start_time__gte=now - timedelta(days=7)
        ).order_by('-start_time')[:5])
    except:
        pass
    
    # Compile context
    context = {
        'user_info': {
            'username': user.username,
            'email': user.email,
            'timezone': str(timezone.get_current_timezone()),
        },
        'schedule_overview': {
            'total_tasks': len(all_tasks),
            'scheduled_tasks': len(scheduled_tasks),
            'unscheduled_tasks': len(unscheduled_tasks),
            'completed_tasks': len([t for t in all_tasks if t.status == 'completed']),
            'total_time_blocks': len(time_blocks),
            'tasks_due_today': len(tasks_due_today),
            'tasks_due_this_week': len(tasks_due_this_week),
            'overdue_tasks': len(overdue_tasks),
        },
        'current_tasks': [
            {
                'id': t.id,
                'title': t.title,
                'description': t.description or '',
                'status': t.status,
                'priority': t.priority,
                'priority_display': t.get_priority_display(),
                'deadline': t.deadline.isoformat(),
                'estimated_hours': float(t.estimated_hours),
                'actual_hours': float(t.actual_hours) if t.actual_hours else None,
                'is_scheduled': t.is_scheduled,
                'start_time': t.start_time.isoformat() if t.start_time else None,
                'end_time': t.end_time.isoformat() if t.end_time else None,
                'is_locked': t.is_locked,
            } for t in all_tasks[:20]  # Limit to recent/important tasks
        ],
        'availability': [
            {
                'id': tb.id,
                'start_time': tb.start_time.isoformat(),
                'end_time': tb.end_time.isoformat(),
                'is_recurring': tb.is_recurring,
                'day_of_week': tb.day_of_week,
                'day_name': tb.get_day_of_week_display() if tb.day_of_week is not None else None,
                'duration_hours': tb.duration_hours,
            } for tb in time_blocks
        ],
        'recent_activity': {
            'recent_optimizations': [
                {
                    'timestamp': opt.timestamp.isoformat(),
                    'scheduled_count': opt.scheduled_count,
                    'unscheduled_count': opt.unscheduled_count,
                    'utilization_rate': opt.utilization_rate,
                    'was_overloaded': opt.was_overloaded,
                } for opt in recent_optimizations
            ],
            'recent_pomodoros': [
                {
                    'task_title': session.task.title,
                    'session_type': session.session_type,
                    'duration': session.actual_duration or session.planned_duration,
                    'start_time': session.start_time.isoformat(),
                    'status': session.status,
                } for session in recent_pomodoros
            ]
        },
        'urgency_analysis': {
            'overdue_tasks': [
                {
                    'title': t.title,
                    'deadline': t.deadline.isoformat(),
                    'priority': t.get_priority_display(),
                    'estimated_hours': float(t.estimated_hours),
                } for t in overdue_tasks[:5]
            ],
            'due_today': [
                {
                    'title': t.title,
                    'deadline': t.deadline.isoformat(),
                    'priority': t.get_priority_display(),
                    'estimated_hours': float(t.estimated_hours),
                } for t in tasks_due_today
            ]
        }
    }
    
    return context
