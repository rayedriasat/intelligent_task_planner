from django import forms
from django.utils import timezone
from datetime import datetime, timedelta, date
from .models import Task, TimeBlock, Habit, HabitEntry, HabitMilestone


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'deadline', 'priority', 
            'estimated_hours', 'min_block_size'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'placeholder': 'Enter task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'rows': 3,
                'placeholder': 'Optional task description'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'step': '0.25',  # Allow quarter-hour increments
                'min': '0.25',   # Minimum 15 minutes
                'max': '24',     # Maximum 24 hours
                'placeholder': 'e.g., 2.5'
            }),
            'min_block_size': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'step': '0.25',  # Allow quarter-hour increments
                'min': '0.25',   # Minimum 15 minutes
                'max': '8',      # Maximum 8-hour blocks
                'placeholder': 'e.g., 0.5'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set priority choices
        self.fields['priority'].choices = [
            (1, 'Low'),
            (2, 'Medium'),
            (3, 'High'),
            (4, 'Urgent'),
        ]
        
        # Make description optional
        self.fields['description'].required = False
        
        # Add helpful help text
        self.fields['estimated_hours'].help_text = "How many hours do you think this task will take? (e.g., 2.5 for 2.5 hours)"
        self.fields['min_block_size'].help_text = "Minimum time block size for this task (e.g., 0.5 for 30 minutes)"

    def clean_estimated_hours(self):
        estimated_hours = self.cleaned_data.get('estimated_hours')
        if estimated_hours is not None:
            if estimated_hours < 0.25:
                raise forms.ValidationError("Estimated hours must be at least 15 minutes (0.25 hours).")
            if estimated_hours > 24:
                raise forms.ValidationError("Estimated hours cannot exceed 24 hours.")
        return estimated_hours

    def clean_min_block_size(self):
        min_block_size = self.cleaned_data.get('min_block_size')
        estimated_hours = self.cleaned_data.get('estimated_hours')
        
        if min_block_size is not None:
            if min_block_size < 0.25:
                raise forms.ValidationError("Minimum block size must be at least 15 minutes (0.25 hours).")
            if min_block_size > 8:
                raise forms.ValidationError("Minimum block size cannot exceed 8 hours.")
            
            # Ensure min_block_size doesn't exceed estimated_hours
            if estimated_hours and min_block_size > estimated_hours:
                raise forms.ValidationError("Minimum block size cannot be larger than estimated hours.")
                
        return min_block_size


class QuickTaskForm(forms.ModelForm):
    """Simplified form for quick task creation during onboarding"""
    class Meta:
        model = Task
        fields = ['title', 'deadline', 'estimated_hours']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'placeholder': "What's your most urgent task?"
            }),
            'deadline': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'step': '0.5',
                'min': '0.1',
                'placeholder': '2.0'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default deadline to tomorrow
        tomorrow = timezone.now() + timedelta(days=1)
        self.fields['deadline'].initial = tomorrow.strftime('%Y-%m-%dT%H:%M')


class TimeBlockForm(forms.ModelForm):
    class Meta:
        model = TimeBlock
        fields = ['start_time', 'end_time', 'is_recurring', 'day_of_week']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }),
            'is_recurring': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'day_of_week': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        is_recurring = cleaned_data.get('is_recurring')
        day_of_week = cleaned_data.get('day_of_week')

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")

        if is_recurring and day_of_week is None:
            raise forms.ValidationError("Day of week is required for recurring time blocks.")

        return cleaned_data


class PdfScheduleForm(forms.Form):
    """Form for selecting date range for PDF schedule export"""
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
        }),
        help_text="Select the start date for your schedule"
    )
    
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
        }),
        help_text="Select the end date for your schedule"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default to current week
        today = timezone.now().date()
        # Calculate start of current week (Monday)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        self.fields['start_date'].initial = start_of_week
        self.fields['end_date'].initial = end_of_week
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("Start date must be before or equal to end date.")
            
            # Limit to maximum of 4 weeks for performance
            if (end_date - start_date).days > 28:
                raise forms.ValidationError("Date range cannot exceed 4 weeks.")
        
        return cleaned_data


# Habit Forms

class HabitForm(forms.ModelForm):
    """Form for creating and editing habits."""
    
    class Meta:
        model = Habit
        fields = [
            'title', 'description', 'category', 'target_frequency', 
            'target_count', 'unit', 'goal_description', 'target_streak', 'color'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'placeholder': 'e.g., Read for 30 minutes, Drink 8 glasses of water'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'rows': 3,
                'placeholder': 'Optional details about your habit'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }),
            'target_frequency': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }),
            'target_count': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'min': '1',
                'placeholder': '1'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'placeholder': 'e.g., minutes, pages, cups, times'
            }),
            'goal_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'rows': 2,
                'placeholder': 'Why is this habit important to you?'
            }),
            'target_streak': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'min': '1',
                'placeholder': 'e.g., 30 for 30-day streak'
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'w-20 h-12 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make optional fields actually optional
        self.fields['description'].required = False
        self.fields['unit'].required = False
        self.fields['goal_description'].required = False
        self.fields['target_streak'].required = False
        
        # Add help text
        self.fields['target_count'].help_text = "How many times should this be done per frequency period?"
        self.fields['unit'].help_text = "Optional: What unit are you measuring? (e.g., minutes, pages, cups)"
        self.fields['target_streak'].help_text = "Optional: Set a streak goal (e.g., 30 days in a row)"
        self.fields['color'].help_text = "Choose a color to represent this habit in visualizations"
    
    def clean_target_count(self):
        target_count = self.cleaned_data.get('target_count')
        if target_count is not None and target_count < 1:
            raise forms.ValidationError("Target count must be at least 1.")
        return target_count
    
    def clean_target_streak(self):
        target_streak = self.cleaned_data.get('target_streak')
        if target_streak is not None and target_streak < 1:
            raise forms.ValidationError("Target streak must be at least 1 day.")
        return target_streak


class QuickHabitForm(forms.ModelForm):
    """Simplified form for quick habit creation."""
    
    class Meta:
        model = Habit
        fields = ['title', 'category', 'target_frequency']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'placeholder': 'e.g., Exercise, Read, Meditate'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }),
            'target_frequency': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }),
        }


class HabitEntryForm(forms.ModelForm):
    """Form for updating habit entries."""
    
    class Meta:
        model = HabitEntry
        fields = ['is_completed', 'count', 'notes']
        widgets = {
            'is_completed': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'count': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'min': '0',
                'placeholder': '1'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'rows': 2,
                'placeholder': 'Optional notes about today\'s progress'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.habit = kwargs.pop('habit', None)
        super().__init__(*args, **kwargs)
        
        # Make notes optional
        self.fields['notes'].required = False
        
        # Set default count based on habit target
        if self.habit and not self.instance.pk:
            self.fields['count'].initial = self.habit.target_count
    
    def clean_count(self):
        count = self.cleaned_data.get('count')
        if count is not None and count < 0:
            raise forms.ValidationError("Count cannot be negative.")
        return count


class HabitMilestoneForm(forms.ModelForm):
    """Form for creating custom habit milestones."""
    
    class Meta:
        model = HabitMilestone
        fields = ['milestone_type', 'title', 'description', 'target_value']
        widgets = {
            'milestone_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'placeholder': 'e.g., 30-Day Streak, 100 Completions'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'rows': 2,
                'placeholder': 'Optional description of this milestone'
            }),
            'target_value': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
                'min': '1',
                'placeholder': '30'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make description optional
        self.fields['description'].required = False
        
        # Add help text
        self.fields['target_value'].help_text = "Target value to achieve (days for streak, count for total, percentage for consistency)"
    
    def clean_target_value(self):
        target_value = self.cleaned_data.get('target_value')
        milestone_type = self.cleaned_data.get('milestone_type')
        
        if target_value is not None:
            if target_value < 1:
                raise forms.ValidationError("Target value must be at least 1.")
            
            # Additional validation based on milestone type
            if milestone_type == 'consistency' and target_value > 100:
                raise forms.ValidationError("Consistency milestone cannot exceed 100%.")
        
        return target_value


class DateRangeForm(forms.Form):
    """Form for selecting date ranges for habit analytics."""
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
        }),
        help_text="Select the start date for analysis"
    )
    
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
        }),
        help_text="Select the end date for analysis"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default to last 30 days
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        
        self.fields['start_date'].initial = thirty_days_ago
        self.fields['end_date'].initial = today
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("Start date must be before or equal to end date.")
            
            # Limit to maximum of 1 year for performance
            if (end_date - start_date).days > 365:
                raise forms.ValidationError("Date range cannot exceed 1 year.")
        
        return cleaned_data
