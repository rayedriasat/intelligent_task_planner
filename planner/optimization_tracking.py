"""
Enhanced optimization tracking for the re-optimize functionality.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class OptimizationHistory(models.Model):
    """Track optimization runs for undo functionality and analysis."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='optimization_history')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optimization results
    scheduled_count = models.IntegerField()
    unscheduled_count = models.IntegerField()
    utilization_rate = models.FloatField()
    total_hours_scheduled = models.FloatField()
    
    # Analysis data
    was_overloaded = models.BooleanField(default=False)
    overload_ratio = models.FloatField(null=True, blank=True)
    excess_hours = models.FloatField(null=True, blank=True)
    
    # Store task state before optimization (for undo)
    previous_task_state = models.JSONField(help_text="JSON snapshot of task scheduling before optimization")
    
    # Store optimization decisions
    optimization_decisions = models.JSONField(help_text="Detailed decisions made during optimization")
    
    # Store recommendations
    recommendations = models.JSONField(default=list, help_text="Optimization recommendations")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Optimization histories"
    
    def __str__(self):
        return f"Optimization {self.id} - {self.timestamp.strftime('%Y-%m-%d %H:%M')} ({self.scheduled_count} tasks)"
    
    @property
    def can_undo(self):
        """Check if this optimization can be undone (within last hour)."""
        return (timezone.now() - self.timestamp).total_seconds() < 3600  # 1 hour limit
    
    def create_task_snapshot(self, user):
        """Create a snapshot of current task scheduling state."""
        tasks_data = []
        for task in user.tasks.filter(status__in=['todo', 'in_progress']):
            tasks_data.append({
                'id': task.id,
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None,
                'is_locked': task.is_locked,
                'status': task.status,
            })
        return tasks_data
    
    def restore_task_state(self):
        """Restore tasks to their previous state (undo optimization)."""
        from planner.models import Task
        
        for task_data in self.previous_task_state:
            try:
                task = Task.objects.get(id=task_data['id'], user=self.user)
                
                # Restore scheduling state
                if task_data['start_time']:
                    task.start_time = timezone.datetime.fromisoformat(task_data['start_time'])
                else:
                    task.start_time = None
                    
                if task_data['end_time']:
                    task.end_time = timezone.datetime.fromisoformat(task_data['end_time'])
                else:
                    task.end_time = None
                
                task.is_locked = task_data['is_locked']
                task.status = task_data['status']
                task.save()
                
            except Task.DoesNotExist:
                continue  # Task was deleted, skip
        
        return True