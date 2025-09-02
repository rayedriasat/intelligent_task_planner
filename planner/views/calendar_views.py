from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'planner/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get week from URL parameter or default to current week
        week_param = self.request.GET.get('week')
        if week_param:
            try:
                base_date = datetime.strptime(week_param, '%Y-%m-%d').date()
            except ValueError:
                base_date = timezone.now().date()
        else:
            base_date = timezone.now().date()
        
        # Calculate week start (Monday) and end (Sunday)
        week_start = base_date - timedelta(days=base_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Get user's tasks for this week using datetime range instead of date range
        # to avoid MySQL timezone conversion issues
        week_start_dt = timezone.make_aware(datetime.combine(week_start, datetime.min.time()))
        week_end_dt = timezone.make_aware(datetime.combine(week_end, datetime.max.time()))
        
        scheduled_tasks = self.request.user.tasks.filter(
            start_time__gte=week_start_dt,
            start_time__lte=week_end_dt
        ).order_by('start_time')

        unscheduled_tasks = self.request.user.tasks.filter(
            start_time__isnull=True,
            status__in=['todo', 'in_progress']
        ).order_by('deadline')

        # Generate week days with tasks
        week_days = []
        today = timezone.now().date()
        for i in range(7):
            day = week_start + timedelta(days=i)
            # Filter tasks for this day from the already-fetched scheduled_tasks
            # to avoid timezone conversion issues
            day_tasks = []
            for task in scheduled_tasks:
                if task.start_time.date() == day:
                    # Convert UTC time to local timezone for positioning
                    local_start_time = task.start_time
                    if timezone.is_aware(local_start_time):
                        # Convert to the Django configured timezone
                        local_start_time = timezone.localtime(local_start_time)
                    
                    # Calculate task position (6 AM = position 0)
                    task_hour = local_start_time.hour
                    task_minute = local_start_time.minute
                    
                    # Position relative to 6 AM (our first hour) 
                    # Each hour slot is 4rem tall
                    if task_hour >= 6:  # Only show tasks from 6 AM onwards
                        position_hours = task_hour - 6  # Hours since 6 AM
                        position_minutes = task_minute / 60.0  # Convert minutes to decimal hours
                        task_top = (position_hours + position_minutes) * 4  # 4rem per hour
                        
                        # Task height based on estimated hours
                        task_height = float(task.estimated_hours) * 4  # 4rem per hour
                        
                        # Add positioning data to task
                        task.position_top = task_top
                        task.position_height = task_height
                        day_tasks.append(task)
            
            week_days.append({
                'date': day,
                'day_name': day.strftime('%A'),
                'day_short': day.strftime('%a'),
                'day_num': day.day,
                'is_today': day == today,
                'tasks': day_tasks
            })

        # Check Google Calendar integration
        from ..models import GoogleCalendarIntegration
        google_integration = GoogleCalendarIntegration.objects.filter(
            user=self.request.user
        ).first()
        
        # Auto-sync disabled - user preference
        # Note: Auto-sync can be re-enabled by uncommenting the code below
        # if (google_integration and google_integration.is_enabled and 
        #     (not google_integration.last_sync or 
        #      timezone.now() - google_integration.last_sync > timedelta(hours=1))):
        #     # Auto-sync code here...
        
        # Calculate navigation dates
        prev_week = week_start - timedelta(days=7)
        next_week = week_start + timedelta(days=7)
        
        # Generate hour range for calendar display (6 AM to 11 PM)
        hours = []
        for hour in range(6, 24):  # 6 AM to 11 PM
            if hour == 0:
                time_label = "12 AM"
            elif hour < 12:
                time_label = f"{hour}:00 AM"
            elif hour == 12:
                time_label = "12 PM"
            else:
                time_label = f"{hour - 12}:00 PM"
            
            hours.append({
                'hour': hour,
                'label': time_label
            })

        context.update({
            'week_start': week_start,
            'week_end': week_end,
            'prev_week': prev_week,
            'next_week': next_week,
            'week_days': week_days,
            'hours': hours,
            'scheduled_tasks': scheduled_tasks,
            'unscheduled_tasks': unscheduled_tasks,
            'google_integration': google_integration,
            'has_google_calendar': google_integration is not None,
        })
        
        return context
