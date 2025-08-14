from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


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
