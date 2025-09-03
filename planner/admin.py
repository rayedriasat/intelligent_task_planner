from django.contrib import admin
from .models import Task, TimeBlock, PomodoroSession, Habit, HabitEntry, HabitMilestone

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


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'target_frequency', 'target_count', 'current_streak', 'completion_rate', 'is_active', 'created_at')
    list_filter = ('category', 'target_frequency', 'is_active', 'created_at', 'user')
    search_fields = ('title', 'description', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'current_streak', 'completion_rate')
    list_editable = ('is_active',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'category', 'color')
        }),
        ('Target Settings', {
            'fields': ('target_frequency', 'target_count', 'unit', 'target_streak')
        }),
        ('Motivation', {
            'fields': ('goal_description',),
            'classes': ('collapse',)
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('current_streak', 'completion_rate'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(HabitEntry)
class HabitEntryAdmin(admin.ModelAdmin):
    list_display = ('habit', 'date', 'is_completed', 'count', 'target_met', 'created_at')
    list_filter = ('is_completed', 'date', 'habit__category', 'habit__user')
    search_fields = ('habit__title', 'habit__user__username', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'target_met')
    date_hierarchy = 'date'
    raw_id_fields = ('habit',)
    
    fieldsets = (
        ('Entry Information', {
            'fields': ('habit', 'date', 'is_completed', 'count')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('habit', 'habit__user')
    
    def target_met(self, obj):
        """Show if target was met for this entry."""
        return obj.is_target_met
    target_met.boolean = True
    target_met.short_description = "Target Met"


@admin.register(HabitMilestone)
class HabitMilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'habit', 'milestone_type', 'target_value', 'is_achieved', 'achieved_at', 'created_at')
    list_filter = ('milestone_type', 'is_achieved', 'created_at', 'achieved_at', 'habit__user')
    search_fields = ('title', 'description', 'habit__title', 'habit__user__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    raw_id_fields = ('habit',)
    
    fieldsets = (
        ('Milestone Information', {
            'fields': ('habit', 'milestone_type', 'title', 'description')
        }),
        ('Target & Achievement', {
            'fields': ('target_value', 'is_achieved', 'achieved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('habit', 'habit__user')
