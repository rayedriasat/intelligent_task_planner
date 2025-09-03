# Import all views for backward compatibility
# This allows existing imports like `from planner.views import TaskCreateView` to continue working

from .task_views import (
    OnboardingView,
    DashboardView,
    KanbanView,
    TaskListView,
    TaskCreateView,
    TaskDetailView,
    TaskUpdateView,
    TaskDeleteView,
    ProfileView,
    bulk_delete_tasks,
    delete_completed_tasks,
)

from .calendar_views import (
    CalendarView,
)

from .scheduling_views import (
    update_task_schedule,
    unschedule_task,
    reoptimize_week,
    undo_optimization,
    reoptimize_schedule,
    auto_schedule_all_tasks,
    quick_schedule_task,
    schedule_urgent_tasks,
    create_urgent_task,
    sacrifice_tasks,
    check_overload,
    compress_schedule,
    prioritize_schedule,
)

from .availability_views import (
    AvailabilityView,
    TimeBlockCreateView,
    TimeBlockDeleteView,
)

from .pomodoro_views import (
    PomodoroTimerView,
    start_pomodoro_session,
    complete_pomodoro_session,
    pause_pomodoro_session,
    cancel_pomodoro_session,
    get_next_session_suggestion,
    start_pomodoro,  # Legacy
    complete_pomodoro,  # Legacy
)

from .api_views import (
    update_task_status,
    toggle_task_status,
    toggle_task_lock,
    update_task_time,
    task_card_partial,
    unscheduled_tasks_partial,
)

from .notification_views import (
    NotificationPreferencesView,
    get_notifications,
    mark_notification_read,
    test_notification,
)

from .ai_views import (
    get_ai_scheduling_suggestions,
    apply_ai_suggestions,
    AIChatView,
    send_ai_chat_message,
)

from .google_calendar_views import (
    GoogleCalendarSettingsView,
    sync_to_google,
    sync_from_google,
    full_sync,
    sync_status,
    toggle_auto_sync,
    GoogleConnectionView,
)

from .canvas_views import (
    CanvasSettingsView,
    canvas_connection_status,
    sync_canvas_assignments,
    sync_canvas_todos,
    sync_canvas_announcements,
    sync_canvas_full,
    canvas_sync_status,
    toggle_canvas_integration,
    CanvasDataView,
    canvas_announcement_to_task,
)

# Expose all views in __all__ for explicit imports
__all__ = [
    # Task views
    'OnboardingView',
    'DashboardView',
    'KanbanView',
    'TaskListView',
    'TaskCreateView',
    'TaskDetailView',
    'TaskUpdateView',
    'TaskDeleteView',
    'ProfileView',
    'bulk_delete_tasks',
    'delete_completed_tasks',
    
    # Calendar views
    'CalendarView',
    
    # Scheduling views
    'update_task_schedule',
    'unschedule_task',
    'reoptimize_week',
    'undo_optimization',
    'reoptimize_schedule',
    'auto_schedule_all_tasks',
    'quick_schedule_task',
    'schedule_urgent_tasks',
    'create_urgent_task',
    'sacrifice_tasks',
    'check_overload',
    'compress_schedule',
    'prioritize_schedule',
    
    # Availability views
    'AvailabilityView',
    'TimeBlockCreateView',
    'TimeBlockDeleteView',
    
    # Pomodoro views
    'PomodoroTimerView',
    'start_pomodoro_session',
    'complete_pomodoro_session',
    'pause_pomodoro_session',
    'cancel_pomodoro_session',
    'get_next_session_suggestion',
    'start_pomodoro',
    'complete_pomodoro',
    
    # API views
    'update_task_status',
    'toggle_task_status',
    'toggle_task_lock',
    'update_task_time',
    'task_card_partial',
    'unscheduled_tasks_partial',
    
    # Notification views
    'NotificationPreferencesView',
    'get_notifications',
    'mark_notification_read',
    'test_notification',
    
    # AI views
    'get_ai_scheduling_suggestions',
    'apply_ai_suggestions',
    'AIChatView',
    'send_ai_chat_message',
    
    # Google Calendar views
    'GoogleCalendarSettingsView',
    'sync_to_google',
    'sync_from_google',
    'full_sync',
    'sync_status',
    'toggle_auto_sync',
    'GoogleConnectionView',
    
    # Canvas LMS views
    'CanvasSettingsView',
    'canvas_connection_status',
    'sync_canvas_assignments',
    'sync_canvas_todos',
    'sync_canvas_announcements',
    'sync_canvas_full',
    'canvas_sync_status',
    'toggle_canvas_integration',
    'CanvasDataView',
    'canvas_announcement_to_task',
]
