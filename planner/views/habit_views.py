from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Q, Avg
from datetime import date, timedelta, datetime
import json
from calendar import monthrange

from ..models import Habit, HabitEntry, HabitMilestone
from ..forms import HabitForm, QuickHabitForm, HabitEntryForm, HabitMilestoneForm, DateRangeForm


class HabitListView(LoginRequiredMixin, ListView):
    """Display all habits for the current user."""
    model = Habit
    template_name = 'planner/habits/habit_list.html'
    context_object_name = 'habits'
    paginate_by = 20

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user, is_active=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_habits = self.get_queryset()
        
        # Calculate summary statistics
        context['total_habits'] = user_habits.count()
        context['active_streaks'] = sum(habit.current_streak for habit in user_habits)
        
        # Get today's completion status for each habit
        today = date.today()
        habits_with_status = []
        for habit in user_habits:
            habit.today_entry = habit.entries.filter(date=today).first()
            habits_with_status.append(habit)
        
        context['habits'] = habits_with_status
        
        # Calculate overall completion rate
        total_entries = HabitEntry.objects.filter(habit__user=self.request.user).count()
        completed_entries = HabitEntry.objects.filter(
            habit__user=self.request.user, 
            is_completed=True
        ).count()
        
        if total_entries > 0:
            context['overall_completion_rate'] = round((completed_entries / total_entries) * 100, 1)
        else:
            context['overall_completion_rate'] = 0
        
        # Get recent achievements
        context['recent_achievements'] = HabitMilestone.objects.filter(
            habit__user=self.request.user,
            is_achieved=True
        ).order_by('-achieved_at')[:3]
        
        return context


class HabitDetailView(LoginRequiredMixin, DetailView):
    """Display detailed view of a specific habit with analytics."""
    model = Habit
    template_name = 'planner/habits/habit_detail.html'
    context_object_name = 'habit'

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        habit = self.object
        
        # Get date range for analytics (default last 30 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Get habit entries for the period
        entries = habit.entries.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        context['entries'] = entries
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        # Calculate analytics
        total_days = (end_date - start_date).days + 1
        completed_days = entries.filter(is_completed=True).count()
        
        context['analytics'] = {
            'total_days': total_days,
            'completed_days': completed_days,
            'completion_rate': round((completed_days / total_days) * 100, 1) if total_days > 0 else 0,
            'current_streak': habit.current_streak,
            'longest_streak': habit.longest_streak,
            'total_completions': habit.entries.filter(is_completed=True).count(),
        }
        
        # Create calendar data for visualization
        calendar_data = self._generate_calendar_data(habit, start_date, end_date)
        context['calendar_data'] = json.dumps(calendar_data)
        
        # Get milestones
        context['milestones'] = habit.milestones.order_by('-is_achieved', 'target_value')
        
        # Check if today's entry exists
        today = date.today()
        context['today_entry'] = habit.entries.filter(date=today).first()
        
        return context
    
    def _generate_calendar_data(self, habit, start_date, end_date):
        """Generate calendar data for JavaScript visualization with proper calendar grid layout."""
        entries_dict = {
            entry.date.isoformat(): {
                'completed': entry.is_completed,
                'count': entry.count,
                'notes': entry.notes or '',
                'has_entry': True  # This date has an actual database entry
            }
            for entry in habit.entries.filter(date__gte=start_date, date__lte=end_date)
        }
        
        calendar_data = []
        current_date = start_date
        
        # Generate data for each day in the specified range
        while current_date <= end_date:
            date_str = current_date.isoformat()
            
            if date_str in entries_dict:
                # Date has an actual entry in the database
                entry_data = entries_dict[date_str]
                calendar_data.append({
                    'date': date_str,
                    'completed': entry_data['completed'],
                    'count': entry_data['count'],
                    'notes': entry_data['notes'],
                    'has_entry': True,
                    'day_of_week': current_date.weekday(),  # 0=Monday, 6=Sunday
                    'day_name': current_date.strftime('%A'),
                    'day_num': current_date.day
                })
            else:
                # Date has no entry in the database (never tracked)
                calendar_data.append({
                    'date': date_str,
                    'completed': False,
                    'count': 0,
                    'notes': '',
                    'has_entry': False,  # No database entry for this date
                    'day_of_week': current_date.weekday(),
                    'day_name': current_date.strftime('%A'),
                    'day_num': current_date.day
                })
            
            current_date += timedelta(days=1)
        
        # Sort calendar data by date to ensure proper order
        calendar_data.sort(key=lambda x: x['date'])
        
        return calendar_data


class HabitCreateView(LoginRequiredMixin, CreateView):
    """Create a new habit."""
    model = Habit
    form_class = HabitForm
    template_name = 'planner/habits/habit_form.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        # Create default milestones
        self._create_default_milestones(self.object)
        
        messages.success(self.request, f'Habit "{self.object.title}" created successfully!')
        return response

    def get_success_url(self):
        return reverse('planner:habit_detail', kwargs={'pk': self.object.pk})
    
    def _create_default_milestones(self, habit):
        """Create default milestones for new habits."""
        default_milestones = [
            {
                'milestone_type': 'streak',
                'title': '7-Day Streak',
                'description': 'Complete this habit for 7 days in a row',
                'target_value': 7
            },
            {
                'milestone_type': 'streak',
                'title': '30-Day Streak',
                'description': 'Complete this habit for 30 days in a row',
                'target_value': 30
            },
            {
                'milestone_type': 'total',
                'title': '100 Completions',
                'description': 'Complete this habit 100 times total',
                'target_value': 100
            },
        ]
        
        for milestone_data in default_milestones:
            HabitMilestone.objects.create(
                habit=habit,
                **milestone_data
            )


class HabitUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing habit."""
    model = Habit
    form_class = HabitForm
    template_name = 'planner/habits/habit_form.html'

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Habit "{self.object.title}" updated successfully!')
        return response

    def get_success_url(self):
        return reverse('planner:habit_detail', kwargs={'pk': self.object.pk})


class HabitDeleteView(LoginRequiredMixin, DeleteView):
    """Soft delete a habit (mark as inactive)."""
    model = Habit
    template_name = 'planner/habits/habit_confirm_delete.html'
    success_url = reverse_lazy('planner:habit_list')

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        # Soft delete - mark as inactive instead of actually deleting
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        
        messages.success(request, f'Habit "{self.object.title}" has been archived.')
        return redirect(self.success_url)


@login_required
def habit_dashboard(request):
    """Main habit tracking dashboard."""
    user_habits = Habit.objects.filter(user=request.user, is_active=True)
    today = date.today()
    
    # Get today's entries for all habits
    today_entries = {}
    for habit in user_habits:
        entry = habit.entries.filter(date=today).first()
        today_entries[habit.id] = entry
    
    # Calculate dashboard statistics
    stats = {
        'total_habits': user_habits.count(),
        'completed_today': sum(1 for entry in today_entries.values() if entry and entry.is_completed),
        'active_streaks': sum(habit.current_streak for habit in user_habits),
        'pending_today': sum(1 for entry in today_entries.values() if not entry or not entry.is_completed),
    }
    
    # Get recent achievements
    recent_achievements = HabitMilestone.objects.filter(
        habit__user=request.user,
        is_achieved=True
    ).order_by('-achieved_at')[:5]
    
    # Weekly completion data for chart
    week_data = []
    for i in range(7):
        check_date = today - timedelta(days=6-i)
        day_entries = HabitEntry.objects.filter(
            habit__user=request.user,
            date=check_date
        )
        completed = day_entries.filter(is_completed=True).count()
        total = day_entries.count()
        
        week_data.append({
            'date': check_date.strftime('%a'),
            'completed': completed,
            'total': total,
            'rate': round((completed / total) * 100, 1) if total > 0 else 0
        })
    
    context = {
        'habits': user_habits,
        'today_entries': today_entries,
        'stats': stats,
        'recent_achievements': recent_achievements,
        'week_data': json.dumps(week_data),
        'today': today,
    }
    
    return render(request, 'planner/habits/habit_dashboard.html', context)


@login_required
def toggle_habit_completion(request, habit_id):
    """Toggle completion status for today's habit entry via AJAX."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"toggle_habit_completion called for habit_id: {habit_id}, user: {request.user}")
    
    if request.method != 'POST':
        logger.warning(f"Invalid method {request.method} for toggle_habit_completion")
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        habit = get_object_or_404(Habit, id=habit_id, user=request.user)
        today = date.today()
        
        logger.info(f"Found habit: {habit.title} for date: {today}")
        
        # Get or create today's entry
        entry, created = HabitEntry.objects.get_or_create(
            habit=habit,
            date=today,
            defaults={'is_completed': False, 'count': 0}
        )
        
        logger.info(f"Entry {'created' if created else 'found'}: completed={entry.is_completed}")
        
        # Toggle completion
        if entry.is_completed:
            entry.is_completed = False
            entry.count = 0
            action = 'uncompleted'
        else:
            entry.is_completed = True
            entry.count = habit.target_count
            action = 'completed'
        
        entry.save()
        logger.info(f"Entry saved: action={action}, completed={entry.is_completed}")
        
        # Check for milestone achievements
        milestones_achieved = []
        try:
            for milestone in habit.milestones.filter(is_achieved=False):
                if milestone.check_and_mark_achieved():
                    milestones_achieved.append(milestone.title)
                    logger.info(f"Milestone achieved: {milestone.title}")
        except Exception as e:
            logger.error(f"Error checking milestones: {e}")
        
        # Get updated stats
        try:
            new_streak = habit.current_streak
            completion_rate = habit.completion_rate
            logger.info(f"Updated stats: streak={new_streak}, completion_rate={completion_rate}")
        except Exception as e:
            logger.error(f"Error calculating stats: {e}")
            new_streak = 0
            completion_rate = 0
        
        response_data = {
            'success': True,
            'action': action,
            'completed': entry.is_completed,
            'current_streak': new_streak,
            'completion_rate': completion_rate,
            'milestones_achieved': milestones_achieved
        }
        
        logger.info(f"Returning successful response: {response_data}")
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in toggle_habit_completion: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@login_required
def update_habit_entry(request, habit_id):
    """Update habit entry with detailed information."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    entry_date = request.POST.get('date')
    
    if not entry_date:
        entry_date = date.today()
    else:
        entry_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
    
    # Get or create entry for the specified date
    entry, created = HabitEntry.objects.get_or_create(
        habit=habit,
        date=entry_date,
        defaults={'is_completed': False, 'count': 0}
    )
    
    form = HabitEntryForm(request.POST, instance=entry, habit=habit)
    
    if form.is_valid():
        form.save()
        
        # Check for milestone achievements if this is today's entry
        milestones_achieved = []
        if entry_date == date.today():
            for milestone in habit.milestones.filter(is_achieved=False):
                if milestone.check_and_mark_achieved():
                    milestones_achieved.append(milestone.title)
        
        return JsonResponse({
            'success': True,
            'completed': entry.is_completed,
            'count': entry.count,
            'notes': entry.notes or '',
            'current_streak': habit.current_streak,
            'completion_rate': habit.completion_rate,
            'milestones_achieved': milestones_achieved
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
def habit_analytics(request, pk):
    """Display detailed analytics for a specific habit."""
    habit = get_object_or_404(Habit, id=pk, user=request.user)
    
    form = DateRangeForm(request.GET or None)
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
    else:
        # Default to last 90 days
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
    
    # Get entries for the period
    entries = habit.entries.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')
    
    # Calculate detailed analytics
    total_days = (end_date - start_date).days + 1
    completed_days = entries.filter(is_completed=True).count()
    
    # Monthly breakdown
    monthly_data = []
    current_month = start_date.replace(day=1)
    
    while current_month <= end_date:
        month_entries = entries.filter(
            date__year=current_month.year,
            date__month=current_month.month
        )
        
        days_in_month = monthrange(current_month.year, current_month.month)[1]
        month_completed = month_entries.filter(is_completed=True).count()
        
        monthly_data.append({
            'month': current_month.strftime('%B %Y'),
            'completed': month_completed,
            'total': min(days_in_month, total_days),
            'rate': round((month_completed / days_in_month) * 100, 1) if days_in_month > 0 else 0
        })
        
        # Move to next month
        if current_month.month == 12:
            current_month = current_month.replace(year=current_month.year + 1, month=1)
        else:
            current_month = current_month.replace(month=current_month.month + 1)
    
    # Streak analysis
    streaks = []
    current_streak = 0
    longest_streak = 0
    
    for entry in entries.order_by('date'):
        if entry.is_completed:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            if current_streak > 0:
                streaks.append(current_streak)
            current_streak = 0
    
    if current_streak > 0:
        streaks.append(current_streak)
    
    analytics = {
        'total_days': total_days,
        'completed_days': completed_days,
        'completion_rate': round((completed_days / total_days) * 100, 1) if total_days > 0 else 0,
        'longest_streak_period': longest_streak,
        'average_streak': round(sum(streaks) / len(streaks), 1) if streaks else 0,
        'total_streaks': len(streaks),
    }
    
    context = {
        'habit': habit,
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'entries': entries,
        'analytics': analytics,
        'monthly_data': json.dumps(monthly_data),
    }
    
    return render(request, 'planner/habits/habit_analytics.html', context)


@login_required
def create_habit_milestone(request, pk):
    """Create a custom milestone for a habit."""
    habit = get_object_or_404(Habit, id=pk, user=request.user)
    
    if request.method == 'POST':
        form = HabitMilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.habit = habit
            milestone.save()
            
            messages.success(request, f'Milestone "{milestone.title}" created successfully!')
            return redirect('planner:habit_detail', pk=habit.id)
    else:
        form = HabitMilestoneForm()
    
    context = {
        'form': form,
        'habit': habit,
    }
    
    return render(request, 'planner/habits/milestone_form.html', context)


@login_required
def quick_add_habit(request):
    """Quick add habit via AJAX."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    form = QuickHabitForm(request.POST)
    
    if form.is_valid():
        habit = form.save(commit=False)
        habit.user = request.user
        habit.save()
        
        return JsonResponse({
            'success': True,
            'habit_id': habit.id,
            'habit_title': habit.title,
            'habit_url': reverse('planner:habit_detail', kwargs={'pk': habit.id})
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
def bulk_update_habits(request):
    """Bulk update multiple habits."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    data = json.loads(request.body)
    habit_updates = data.get('habits', [])
    action = data.get('action')
    
    updated_count = 0
    
    for habit_data in habit_updates:
        habit_id = habit_data.get('id')
        try:
            habit = Habit.objects.get(id=habit_id, user=request.user)
            
            if action == 'mark_complete':
                entry, created = HabitEntry.objects.get_or_create(
                    habit=habit,
                    date=date.today(),
                    defaults={'is_completed': False, 'count': 0}
                )
                if not entry.is_completed:
                    entry.is_completed = True
                    entry.count = habit.target_count
                    entry.save()
                    updated_count += 1
            
            elif action == 'archive':
                habit.is_active = False
                habit.save()
                updated_count += 1
                
        except Habit.DoesNotExist:
            continue
    
    return JsonResponse({
        'success': True,
        'updated_count': updated_count
    })