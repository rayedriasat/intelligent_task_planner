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
    path('calendar/reoptimize/', views.reoptimize_schedule, name='reoptimize_schedule'),
    path('calendar/update-task/', views.update_task_time, name='update_task_time'),
    
    # Time blocks
    path('availability/', views.AvailabilityView.as_view(), name='availability'),
    path('availability/create/', views.TimeBlockCreateView.as_view(), name='timeblock_create'),
    path('availability/<int:pk>/delete/', views.TimeBlockDeleteView.as_view(), name='timeblock_delete'),
    
    # Pomodoro
    path('pomodoro/', views.PomodoroView.as_view(), name='pomodoro'),
    path('pomodoro/start/', views.start_pomodoro, name='start_pomodoro'),
    path('pomodoro/complete/', views.complete_pomodoro, name='complete_pomodoro'),
    
    # API endpoints for HTMX
    path('api/task-card/<int:pk>/', views.task_card_partial, name='task_card_partial'),
    path('api/unscheduled-tasks/', views.unscheduled_tasks_partial, name='unscheduled_tasks_partial'),
]
