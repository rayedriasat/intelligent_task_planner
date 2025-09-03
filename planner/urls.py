from django.urls import path
from . import views
from .manual_scheduling import manual_schedule_task, create_and_schedule_task, unschedule_task as manual_unschedule_task
from .views.pdf_views import SchedulePdfFormView, SchedulePdfGenerateView

app_name = 'planner'

urlpatterns = [
    # Dashboard and main views
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('onboarding/', views.OnboardingView.as_view(), name='onboarding'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Task management
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/<int:pk>/toggle-status/', views.toggle_task_status, name='toggle_task_status'),
    path('tasks/<int:pk>/lock/', views.toggle_task_lock, name='toggle_task_lock'),
    
    # Bulk task operations
    path('api/tasks/bulk-delete/', views.bulk_delete_tasks, name='bulk_delete_tasks'),
    path('api/tasks/delete-completed/', views.delete_completed_tasks, name='delete_completed_tasks'),
    
    # Kanban board
    path('kanban/', views.KanbanView.as_view(), name='kanban'),
    path('kanban/update-status/', views.update_task_status, name='update_task_status'),
    
    # Calendar
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('calendar/update-task/', views.update_task_schedule, name='update_task_schedule'),
    path('calendar/unschedule/', views.unschedule_task, name='unschedule_task'),
    path('calendar/reoptimize/', views.reoptimize_week, name='reoptimize_week'),
    path('calendar/undo-optimization/', views.undo_optimization, name='undo_optimization'),
    path('calendar/auto-schedule-all/', views.auto_schedule_all_tasks, name='auto_schedule_all_tasks'),
    path('calendar/check-overload/', views.check_overload, name='check_overload'),
    path('calendar/compress-schedule/', views.compress_schedule, name='compress_schedule'),
    path('calendar/prioritize-schedule/', views.prioritize_schedule, name='prioritize_schedule'),
    
    # Manual Scheduling
    path('api/manual-schedule/', manual_schedule_task, name='manual_schedule_task'),
    path('api/create-and-schedule/', create_and_schedule_task, name='create_and_schedule_task'),
    path('api/manual-unschedule/', manual_unschedule_task, name='manual_unschedule_task'),

    
    # Time blocks
    path('availability/', views.AvailabilityView.as_view(), name='availability'),
    path('availability/create/', views.TimeBlockCreateView.as_view(), name='timeblock_create'),
    path('availability/<int:pk>/delete/', views.TimeBlockDeleteView.as_view(), name='timeblock_delete'),
    
    # Pomodoro
    path('pomodoro/', views.PomodoroTimerView.as_view(), name='pomodoro'),
    path('pomodoro/start/', views.start_pomodoro_session, name='start_pomodoro_session'),
    path('pomodoro/complete/', views.complete_pomodoro_session, name='complete_pomodoro_session'),
    path('pomodoro/pause/', views.pause_pomodoro_session, name='pause_pomodoro_session'),
    path('pomodoro/cancel/', views.cancel_pomodoro_session, name='cancel_pomodoro_session'),

    # API endpoints for HTMX
    path('api/task-card/<int:pk>/', views.task_card_partial, name='task_card_partial'),
    path('api/unscheduled-tasks/', views.unscheduled_tasks_partial, name='unscheduled_tasks_partial'),
    path('api/quick-schedule/', views.quick_schedule_task, name='quick_schedule_task'),
    path('api/schedule-urgent/', views.schedule_urgent_tasks, name='schedule_urgent_tasks'),
    
    # Sacrifice mode for urgent tasks
    path('api/create-urgent/', views.create_urgent_task, name='create_urgent_task'),
    path('api/sacrifice-tasks/', views.sacrifice_tasks, name='sacrifice_tasks'),
    
    # Notifications
    path('notifications/', views.NotificationPreferencesView.as_view(), name='notification_preferences'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/test/', views.test_notification, name='test_notification'),
    
    # AI Integration
    path('ai-chat/', views.AIChatView.as_view(), name='ai_chat'),
    path('api/ai-chat/', views.send_ai_chat_message, name='send_ai_chat_message'),
    path('api/ai-suggestions/', views.get_ai_scheduling_suggestions, name='get_ai_scheduling_suggestions'),
    path('api/ai-suggestions/apply/', views.apply_ai_suggestions, name='apply_ai_suggestions'),
    
    # Google Calendar Integration
    path('google-calendar/settings/', views.GoogleCalendarSettingsView.as_view(), name='google_calendar_settings'),
    path('google-calendar/connection/', views.GoogleConnectionView.as_view(), name='google_connection'),
    path('google-calendar/sync-to/', views.sync_to_google, name='sync_to_google'),
    path('google-calendar/sync-from/', views.sync_from_google, name='sync_from_google'),
    path('google-calendar/full-sync/', views.full_sync, name='full_sync'),
    path('google-calendar/status/', views.sync_status, name='sync_status'),
    path('google-calendar/toggle-auto/', views.toggle_auto_sync, name='toggle_auto_sync'),
    
    # Canvas LMS Integration
    path('canvas/settings/', views.CanvasSettingsView.as_view(), name='canvas_settings'),
    path('canvas/data/', views.CanvasDataView.as_view(), name='canvas_data'),
    path('canvas/connection-status/', views.canvas_connection_status, name='canvas_connection_status'),
    path('canvas/sync-assignments/', views.sync_canvas_assignments, name='sync_canvas_assignments'),
    path('canvas/sync-todos/', views.sync_canvas_todos, name='sync_canvas_todos'),
    path('canvas/sync-announcements/', views.sync_canvas_announcements, name='sync_canvas_announcements'),
    path('canvas/full-sync/', views.sync_canvas_full, name='sync_canvas_full'),
    path('canvas/status/', views.canvas_sync_status, name='canvas_sync_status'),
    path('canvas/toggle/', views.toggle_canvas_integration, name='toggle_canvas_integration'),
    path('canvas/announcements/<int:announcement_id>/to-task/', views.canvas_announcement_to_task, name='canvas_announcement_to_task'),
    
    # PDF Export
    path('schedule/pdf/', SchedulePdfFormView.as_view(), name='schedule_pdf_form'),
    path('schedule/pdf/generate/<str:start_date>/<str:end_date>/', SchedulePdfGenerateView.as_view(), name='schedule_pdf_generate'),
]
