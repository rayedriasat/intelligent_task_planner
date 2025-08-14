from django.contrib import admin
from .models import Task, TimeBlock, PomodoroSession

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'deadline', 'priority', 'status', 'estimated_hours')
    list_filter = ('status', 'priority', 'user')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_time', 'end_time', 'is_recurring')
    list_filter = ('is_recurring', 'user')

@admin.register(PomodoroSession)
class PomodoroSessionAdmin(admin.ModelAdmin):
    list_display = ('task', 'session_type', 'status', 'planned_duration', 'actual_duration', 'start_time', 'duration_display')
    list_filter = ('session_type', 'status', 'start_time', 'task__user')
    readonly_fields = ('start_time', 'duration_minutes')
    search_fields = ('task__title', 'task__user__username', 'notes')
    raw_id_fields = ('task',)  # Better UX for foreign key selection
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task', 'task__user')
    
    def duration_display(self, obj):
        """Show actual duration if available, otherwise planned duration."""
        if obj.actual_duration:
            return f"{obj.actual_duration} min"
        return f"{obj.planned_duration} min (planned)"
    duration_display.short_description = "Duration"
