from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Task, TimeBlock


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
