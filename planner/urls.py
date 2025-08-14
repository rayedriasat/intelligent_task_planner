from django.urls import path
from . import views

app_name = 'planner'

urlpatterns = [
    # Dashboard and main views
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('onboarding/', views.OnboardingView.as_view(), name='onboarding'),
    
    # Task management
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/<int:pk>/toggle-status/', views.toggle_task_status, name='toggle_task_status'),
    path('tasks/<int:pk>/lock/', views.toggle_task_lock, name='toggle_task_lock'),
    
    # Kanban board
    path('kanban/', views.KanbanView.as_view(), name='kanban'),
    path('kanban/update-status/', views.update_task_status, name='update_task_status'),
    
    # Calendar
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('calendar/update-task/', views.update_task_schedule, name='update_task_schedule'),
    path('calendar/unschedule/', views.unschedule_task, name='unschedule_task'),
    path('calendar/reoptimize/', views.reoptimize_week, name='reoptimize_week'),

    
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
]
