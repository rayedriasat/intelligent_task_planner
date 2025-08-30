from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


class Task(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    deadline = models.DateTimeField()
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2)  # Allows values like 99.75
    min_block_size = models.DecimalField(max_digits=4, decimal_places=2, default=0.5)  # Allows values like 99.75
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['deadline', 'priority']

    def __str__(self):
        return self.title

    @property
    def is_scheduled(self):
        return self.start_time is not None and self.end_time is not None
    
    @property
    def calendar_top_position(self):
        """Calculate top position in pixels for calendar display."""
        if not self.start_time:
            return 0
        # Assuming calendar starts at 7 AM, each hour = 80px
        hour_offset = self.start_time.hour - 7
        minute_offset = self.start_time.minute
        return (hour_offset * 80) + (minute_offset * 80 / 60)
    
    @property
    def calendar_height(self):
        """Calculate height in pixels based on estimated hours."""
        if not self.estimated_hours:
            return 60  # minimum height
        return max(float(self.estimated_hours) * 80, 60)
    
    @property
    def calendar_left_position(self):
        """Calculate left position for day of week."""
        if not self.start_time:
            return 0
        day_of_week = self.start_time.weekday()  # Monday = 0
        return f"calc(5rem + {day_of_week} * (100% - 5rem) / 7)"
    
    @property
    def calendar_width(self):
        """Calculate width for calendar task block."""
        return "calc((100% - 5rem) / 7 - 4px)"


class TimeBlock(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_blocks')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_recurring = models.BooleanField(default=False)
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'start_time', 'end_time']),
            models.Index(fields=['user', 'is_recurring']),
        ]

    def __str__(self):
        if self.is_recurring:
            return f"{self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
        return f"{self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}"

    @property
    def duration_hours(self):
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600

# Add this new model to your existing models.py

class PomodoroSession(models.Model):
    """Model for tracking Pomodoro focus sessions."""
    
    SESSION_TYPES = [
        ('focus', 'Focus Session'),
        ('short_break', 'Short Break'),
        ('long_break', 'Long Break'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='pomodoro_sessions')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='focus')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    planned_duration = models.IntegerField(default=25)  # Duration in minutes
    actual_duration = models.IntegerField(null=True, blank=True)  # Actual time spent
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.get_session_type_display()} - {self.task.title}"
    
    @property
    def duration_minutes(self):
        """Get actual duration in minutes if completed."""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return None
    
    @property
    def is_active(self):
        """Check if session is currently active."""
        return self.status == 'active'


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


class NotificationPreference(models.Model):
    """User notification preferences."""
    
    NOTIFICATION_TYPES = [
        ('task_reminder', 'Task Reminder'),
        ('deadline_warning', 'Deadline Warning'),
        ('schedule_optimization', 'Schedule Optimization'),
        ('pomodoro_break', 'Pomodoro Break'),
    ]
    
    DELIVERY_METHODS = [
        ('browser', 'Browser Push'),
        ('email', 'Email'),
        ('both', 'Browser + Email'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Notification type preferences
    task_reminder_enabled = models.BooleanField(default=True)
    task_reminder_minutes = models.IntegerField(default=60, help_text='Minutes before task start')
    task_reminder_method = models.CharField(max_length=10, choices=DELIVERY_METHODS, default='browser')
    
    deadline_warning_enabled = models.BooleanField(default=True)
    deadline_warning_hours = models.IntegerField(default=24, help_text='Hours before deadline')
    deadline_warning_method = models.CharField(max_length=10, choices=DELIVERY_METHODS, default='both')
    
    schedule_optimization_enabled = models.BooleanField(default=True)
    schedule_optimization_method = models.CharField(max_length=10, choices=DELIVERY_METHODS, default='browser')
    
    pomodoro_break_enabled = models.BooleanField(default=True)
    
    # Global settings
    email_notifications_enabled = models.BooleanField(default=True)
    browser_notifications_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create notification preferences for a user."""
        prefs, created = cls.objects.get_or_create(user=user)
        return prefs


class TaskNotification(models.Model):
    """Track sent notifications to avoid duplicates."""
    
    NOTIFICATION_TYPES = [
        ('task_reminder', 'Task Reminder'),
        ('deadline_warning', 'Deadline Warning'),
        ('schedule_optimization', 'Schedule Optimization'),
        ('pomodoro_break', 'Pomodoro Break'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    scheduled_time = models.DateTimeField()
    sent_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_method = models.CharField(max_length=10, default='browser')
    
    # Message content
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Tracking
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_time']
        indexes = [
            models.Index(fields=['task', 'notification_type', 'status']),
            models.Index(fields=['scheduled_time', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.task.title}"
    
    def mark_as_sent(self):
        """Mark notification as successfully sent."""
        self.status = 'sent'
        self.sent_time = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message):
        """Mark notification as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.save()


# Signal handlers for automatic notification scheduling
@receiver(post_save, sender=Task)
def handle_task_save(sender, instance, created, **kwargs):
    """Handle task creation and updates to manage notifications."""
    # Import here to avoid circular imports
    from .services.notification_service import NotificationService
    
    # If task has a start_time (is scheduled), schedule notifications
    if instance.start_time:
        # Cancel any existing notifications first
        NotificationService.cancel_task_notifications(instance)
        
        # Schedule new notifications
        NotificationService.schedule_task_reminders(instance)


@receiver(pre_save, sender=Task)
def handle_task_pre_save(sender, instance, **kwargs):
    """Handle task updates to cancel notifications if task is unscheduled."""
    if instance.pk:  # Only for existing tasks
        try:
            old_instance = Task.objects.get(pk=instance.pk)
            
            # If task was scheduled but now is not, cancel notifications
            if old_instance.start_time and not instance.start_time:
                from .services.notification_service import NotificationService
                NotificationService.cancel_task_notifications(instance)
                
        except Task.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create notification preferences for new users."""
    if created:
        NotificationPreference.objects.create(user=instance)
