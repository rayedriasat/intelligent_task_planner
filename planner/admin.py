from django.contrib import admin
from .models import Task, TimeBlock, PomodoroSession


# Register your models here.

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'priority', 'deadline', 'estimated_hours', 'is_locked']
    list_filter = ['status', 'priority', 'is_locked', 'created_at']
    search_fields = ['title', 'description', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'status')
        }),
        ('Scheduling', {
            'fields': ('deadline', 'priority', 'estimated_hours', 'min_block_size', 'start_time', 'end_time', 'is_locked')
        }),
        ('Progress', {
            'fields': ('actual_hours',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    list_display = ['user', 'start_time', 'end_time', 'is_recurring', 'day_of_week']
    list_filter = ['is_recurring', 'day_of_week', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(PomodoroSession)
class PomodoroSessionAdmin(admin.ModelAdmin):
    list_display = ['task', 'start_time', 'end_time', 'duration_minutes']
    list_filter = ['created_at']
    search_fields = ['task__title', 'task__user__email']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task', 'task__user')

    def duration_minutes(self, obj):
        return f"{obj.duration_minutes:.1f} min"
    duration_minutes.short_description = 'Duration'
