from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from django.utils import timezone
from ..models import Task, TimeBlock


class SchedulingEngine:
    """
    Core scheduling engine that handles task placement and optimization.
    This is the heart of the application's intelligence.
    """

    def __init__(self, user):
        self.user = user

    def schedule_urgent_tasks(self, urgent_tasks: List[Task]) -> Tuple[List[Task], List[Task]]:
        """
        Schedule urgent tasks with deadline constraints.
        Now uses the consistent calculate_schedule method for better reliability.
        """
        if not urgent_tasks:
            return [], []
        
        # Use the main calculate_schedule method which now handles urgency properly
        return self.calculate_schedule(tasks=urgent_tasks)

    def calculate_schedule(self, tasks: List[Task] = None, time_blocks: List[TimeBlock] = None) -> Tuple[List[Task], List[Task]]:
        """
        Main scheduling function that takes tasks and time blocks,
        returns scheduled and unscheduled tasks.
        NOW SUPPORTS URGENCY AND DEADLINE CONSTRAINTS FOR CONSISTENCY.
        """
        if tasks is None:
            tasks = list(self.user.tasks.filter(status__in=['todo', 'in_progress'], is_locked=False))
        
        if time_blocks is None:
            time_blocks = list(self.user.time_blocks.all())

        # Create available time slots from time blocks
        available_slots = self._generate_available_slots(time_blocks)
        
        # Separate urgent and regular tasks for proper prioritization
        now = timezone.now()
        urgent_deadline = now + timedelta(hours=24)
        
        urgent_tasks = []
        regular_tasks = []
        
        for task in tasks:
            if (task.deadline and task.deadline <= urgent_deadline and task.deadline > now) or task.priority == 4:
                urgent_tasks.append(task)
            else:
                regular_tasks.append(task)
        
        # Sort urgent tasks by deadline (most urgent first), then regular tasks by priority
        urgent_tasks_sorted = sorted(urgent_tasks, key=lambda t: (t.deadline or now + timedelta(days=365), -t.priority))
        
        # For regular tasks, sort by priority (1=low, 2=medium, 3=high, 4=urgent already filtered out)
        # Higher priority numbers should be scheduled first: 3 (high) → 2 (medium) → 1 (low)
        regular_tasks_sorted = sorted(regular_tasks, key=lambda t: -t.priority)
        
        # Combine with urgent tasks first
        tasks_to_schedule = urgent_tasks_sorted + regular_tasks_sorted

        scheduled_tasks = []
        unscheduled_tasks = []

        # Check for overload before scheduling
        total_required_hours = sum(t.estimated_hours for t in tasks_to_schedule)
        total_available_hours = sum(self._slot_duration(slot) for slot in available_slots)

        if total_required_hours > total_available_hours:
            # Handle overload scenario
            return self._handle_overload(tasks_to_schedule, available_slots)

        # Schedule tasks with deadline awareness
        latest_end_time = now  # Track the latest end time for sequential scheduling
        
        for i, task in enumerate(tasks_to_schedule):
            # Find a slot that starts after the latest scheduled end time
            scheduled_slot = self._find_suitable_slot_sequential(task, available_slots, latest_end_time)
            
            if scheduled_slot:
                # Schedule the task
                task.start_time = scheduled_slot['start']
                task.end_time = scheduled_slot['end']
                scheduled_tasks.append(task)
                
                # Update the latest end time for the next task
                latest_end_time = scheduled_slot['end']
                
                # Remove or split the used slot
                available_slots = self._update_available_slots(available_slots, scheduled_slot)
            else:
                unscheduled_tasks.append(task)

        return scheduled_tasks, unscheduled_tasks

    def _generate_available_slots(self, time_blocks: List[TimeBlock], end_date=None) -> List[dict]:
        """Generate available time slots from time blocks with calendar view constraints (6 AM - 12 AM)."""
        now = timezone.now()
        
        # If no end_date specified, default to one week from now
        if end_date is None:
            end_date = (now + timedelta(days=7)).date()
        
        # Start from today, not the Monday of current week
        start_date = now.date()
        
        # Calendar view constraints: 6 AM to Midnight (next day 00:00)
        CALENDAR_START_HOUR = 6  # 6 AM
        
        slots = []
        
        for block in time_blocks:
            if block.is_recurring:
                # Generate slots for each day from start_date to end_date
                current_date = start_date
                while current_date <= end_date:
                    if block.day_of_week == current_date.weekday():
                        slot_start = timezone.make_aware(datetime.combine(
                            current_date,
                            block.start_time.time()
                        ))
                        slot_end = timezone.make_aware(datetime.combine(
                            current_date,
                            block.end_time.time()
                        ))
                        
                        # Apply calendar view constraints (6 AM - 12 AM)
                        day_calendar_start = timezone.make_aware(datetime.combine(
                            current_date, 
                            datetime.min.time().replace(hour=CALENDAR_START_HOUR)
                        ))
                        # For end time, use next day at midnight (hour 0)
                        next_day = current_date + timedelta(days=1)
                        day_calendar_end = timezone.make_aware(datetime.combine(
                            next_day, 
                            datetime.min.time()  # This is midnight (00:00) of next day
                        ))
                        
                        # Constrain slot to calendar view hours
                        constrained_start = max(slot_start, day_calendar_start)
                        constrained_end = min(slot_end, day_calendar_end)
                        
                        if constrained_end > constrained_start and constrained_end > now:
                            # Add the slot with its original time - we'll handle current time later
                            slots.append({
                                'start': constrained_start,
                                'end': constrained_end,
                                'block_id': block.id
                            })
                    current_date += timedelta(days=1)
            else:
                # Single occurrence - check if it ends in the future and within our date range
                if (block.end_time > now and 
                    start_date <= block.start_time.date() <= end_date):
                    
                    # Apply calendar view constraints for single occurrences too
                    block_date = block.start_time.date()
                    day_calendar_start = timezone.make_aware(datetime.combine(
                        block_date, 
                        datetime.min.time().replace(hour=CALENDAR_START_HOUR)
                    ))
                    # For end time, use next day at midnight (hour 0)
                    next_day = block_date + timedelta(days=1)
                    day_calendar_end = timezone.make_aware(datetime.combine(
                        next_day, 
                        datetime.min.time()  # This is midnight (00:00) of next day
                    ))
                    
                    # Constrain to calendar view
                    constrained_start = max(block.start_time, day_calendar_start)
                    constrained_end = min(block.end_time, day_calendar_end)
                    
                    if constrained_end > constrained_start:
                        # Add the slot with its original time - we'll handle current time later
                        slots.append({
                            'start': constrained_start,
                            'end': constrained_end,
                            'block_id': block.id
                        })

        # Adjust slots that start in the past to start at current time
        now = timezone.now()
        adjusted_slots = []
        for slot in slots:
            if slot['start'] < now < slot['end']:
                # Current time is within this slot - adjust start to current time
                adjusted_slots.append({
                    'start': now,
                    'end': slot['end'],
                    'block_id': slot['block_id']
                })
            elif slot['end'] > now:
                # Slot is completely in the future - keep as is
                adjusted_slots.append(slot)
            # Skip slots that are completely in the past
        
        slots = adjusted_slots

        # Remove conflicts with existing scheduled tasks
        scheduled_tasks = self.user.tasks.filter(
            start_time__isnull=False,
            end_time__isnull=False,
            status__in=['todo', 'in_progress']
        )
        
        # Remove conflicts with ALL scheduled tasks, not just locked ones
        for task in scheduled_tasks:
            slots = self._remove_conflicts(slots, task.start_time, task.end_time)

        return sorted(slots, key=lambda x: x['start'])

    def _find_suitable_slot(self, task: Task, available_slots: List[dict]) -> Optional[dict]:
        """Find a suitable time slot for the given task that respects the deadline."""
        
        # Convert Decimal to float for timedelta
        required_duration = timedelta(hours=float(task.estimated_hours))
        min_duration = timedelta(hours=float(task.min_block_size))
        
        # Task deadline constraint - task must be completed BEFORE the deadline
        task_deadline = task.deadline
        
        # Sort slots by date first, then by time
        # But prefer slots that can fit after already scheduled tasks on the same day
        def sort_key(slot):
            # Get date and time
            slot_date = slot['start'].date()
            slot_time = slot['start'].time()
            
            # For sequential scheduling, we want to prioritize slots that start after the current time
            # within the same day first, then move to the next day
            return (slot_date, slot_time)
        
        sorted_slots = sorted(available_slots, key=sort_key)
        
        for slot in sorted_slots:
            slot_duration = slot['end'] - slot['start']
            
            # CRITICAL: Check if the slot can complete BEFORE the deadline
            if task_deadline and slot['start'] >= task_deadline:
                # Slot starts after deadline - skip this slot
                continue
            
            # Check if we have enough time to complete before deadline
            if task_deadline:
                latest_end_time = min(slot['end'], task_deadline)
            else:
                latest_end_time = slot['end']
                
            available_time_before_deadline = latest_end_time - slot['start']
            
            # Check if slot is big enough for minimum block size and fits before deadline
            if available_time_before_deadline >= min_duration:
                # Check if we can fit the full task before deadline
                if available_time_before_deadline >= required_duration:
                    # Schedule for the full duration, ending before deadline
                    return {
                        'start': slot['start'],
                        'end': slot['start'] + required_duration,
                        'block_id': slot['block_id']
                    }
                else:
                    # Can fit minimum block but not full task, schedule what fits before deadline
                    return {
                        'start': slot['start'],
                        'end': latest_end_time,
                        'block_id': slot['block_id']
                    }
        
        return None

    def _find_suitable_slot_sequential(self, task: Task, available_slots: List[dict], earliest_start_time: datetime) -> Optional[dict]:
        """Find a suitable time slot for sequential scheduling that starts after the given time."""
        
        # Convert Decimal to float for timedelta
        required_duration = timedelta(hours=float(task.estimated_hours))
        min_duration = timedelta(hours=float(task.min_block_size))
        
        # Task deadline constraint - task must be completed BEFORE the deadline
        task_deadline = task.deadline
        
        # Sort slots by date first, then by time
        def sort_key(slot):
            slot_date = slot['start'].date()
            slot_time = slot['start'].time()
            return (slot_date, slot_time)
        
        sorted_slots = sorted(available_slots, key=sort_key)
        
        for slot in sorted_slots:
            # The slot must start at or after the earliest_start_time
            effective_start = max(slot['start'], earliest_start_time)
            
            # Check if the effective start time is still within the slot
            if effective_start >= slot['end']:
                continue  # This slot is too early, skip it
            
            slot_duration = slot['end'] - effective_start
            
            # CRITICAL: Check if the slot can complete BEFORE the deadline
            if task_deadline and effective_start >= task_deadline:
                # Slot starts after deadline - skip this slot
                continue
            
            # Check if we have enough time to complete before deadline
            if task_deadline:
                latest_end_time = min(slot['end'], task_deadline)
            else:
                latest_end_time = slot['end']
                
            available_time_before_deadline = latest_end_time - effective_start
            
            # Check if slot is big enough for minimum block size and fits before deadline
            if available_time_before_deadline >= min_duration:
                # Check if we can fit the full task before deadline
                if available_time_before_deadline >= required_duration:
                    # Schedule for the full duration, ending before deadline
                    return {
                        'start': effective_start,
                        'end': effective_start + required_duration,
                        'block_id': slot['block_id']
                    }
                else:
                    # Can fit minimum block but not full task, schedule what fits before deadline
                    return {
                        'start': effective_start,
                        'end': latest_end_time,
                        'block_id': slot['block_id']
                    }
        
        return None

    def _update_available_slots(self, slots: List[dict], used_slot: dict) -> List[dict]:
        """Update available slots after scheduling a task."""
        updated_slots = []
        
        for slot in slots:
            # Check if this slot overlaps with the used slot
            if (slot['start'] < used_slot['end'] and slot['end'] > used_slot['start'] and 
                slot['block_id'] == used_slot['block_id']):
                # This slot overlaps with the used slot - split it
                
                if slot['start'] < used_slot['start']:
                    # There's time before the used slot
                    before_slot = {
                        'start': slot['start'],
                        'end': used_slot['start'],
                        'block_id': slot['block_id']
                    }
                    updated_slots.append(before_slot)
                
                if used_slot['end'] < slot['end']:
                    # There's time after the used slot
                    after_slot = {
                        'start': used_slot['end'],
                        'end': slot['end'],
                        'block_id': slot['block_id']
                    }
                    updated_slots.append(after_slot)
            else:
                # Keep other slots as is (no overlap or different block)
                updated_slots.append(slot)
        
        return updated_slots

    def _remove_conflicts(self, slots: List[dict], start_time: datetime, end_time: datetime) -> List[dict]:
        """Remove or split slots that conflict with a scheduled task."""
        updated_slots = []
        
        for slot in slots:
            # Check for overlap
            if start_time >= slot['end'] or end_time <= slot['start']:
                # No overlap
                updated_slots.append(slot)
            else:
                # There is overlap, split the slot
                if slot['start'] < start_time:
                    # Add the part before the conflict
                    updated_slots.append({
                        'start': slot['start'],
                        'end': start_time,
                        'block_id': slot['block_id']
                    })
                
                if end_time < slot['end']:
                    # Add the part after the conflict
                    updated_slots.append({
                        'start': end_time,
                        'end': slot['end'],
                        'block_id': slot['block_id']
                    })
        
        return updated_slots

    def _handle_overload(self, tasks: List[Task], available_slots: List[dict]) -> Tuple[List[Task], List[Task]]:
        """Handle the case when total task time exceeds available time."""
        # For now, schedule high-priority tasks first until we run out of time
        scheduled_tasks = []
        unscheduled_tasks = []
        
        remaining_slots = available_slots.copy()
        
        for task in tasks:
            scheduled_slot = self._find_suitable_slot(task, remaining_slots)
            
            if scheduled_slot:
                task.start_time = scheduled_slot['start']
                task.end_time = scheduled_slot['end']
                scheduled_tasks.append(task)
                remaining_slots = self._update_available_slots(remaining_slots, scheduled_slot)
            else:
                unscheduled_tasks.append(task)
        
        return scheduled_tasks, unscheduled_tasks

    def _slot_duration(self, slot: dict) -> float:
        """Calculate duration of a slot in hours."""
        delta = slot['end'] - slot['start']
        return delta.total_seconds() / 3600

    def reschedule_week(self) -> Tuple[List[Task], List[Task]]:
        """Re-optimize the entire week's schedule."""
        # Clear existing schedule for unlocked tasks
        tasks_to_reschedule = self.user.tasks.filter(
            status__in=['todo', 'in_progress'],
            is_locked=False
        )
        
        for task in tasks_to_reschedule:
            task.start_time = None
            task.end_time = None
            task.save()  # Save the changes to database
        
        # Recalculate schedule
        return self.calculate_schedule()

    def _calculate_task_priority_score(self, task: Task) -> tuple:
        """
        Calculate enhanced priority score for better task ordering.
        Returns tuple for sorting: (urgency_score, priority_score, size_score)
        Lower scores = higher priority (scheduled first)
        """
        now = timezone.now()
        
        # Calculate deadline urgency (days until deadline)
        if task.deadline:
            time_until_deadline = (task.deadline - now).total_seconds() / (24 * 3600)  # days
            urgency_score = max(0, time_until_deadline)  # Closer deadlines = lower score
        else:
            # No deadline = low urgency (higher score, scheduled later)
            urgency_score = 999999  # Very high score = low priority
        
        # Priority score (1=high priority, 4=low priority, so lower is better)
        priority_score = task.priority
        
        # Size score - prefer to schedule smaller tasks first for better scheduling efficiency
        size_score = float(task.estimated_hours)
        
        return (urgency_score, priority_score, size_score)

    def _find_suitable_slot_with_splitting(self, task: Task, available_slots: List[dict]) -> List[dict]:
        """
        Advanced slot finding with intelligent task splitting.
        Returns a list of time slots that can accommodate the task (possibly split).
        """
        required_hours = float(task.estimated_hours)
        min_block_hours = float(task.min_block_size)
        
        # Try to find a single slot that fits the entire task first
        single_slot = self._find_suitable_slot(task, available_slots)
        if single_slot and self._slot_duration(single_slot) >= required_hours:
            # Found a slot that can fit the whole task
            return [single_slot]
        
        # If no single slot works, try to split the task across multiple slots
        suitable_slots = []
        remaining_hours = required_hours
        
        # Sort slots by start time to schedule in chronological order
        sorted_slots = sorted(available_slots, key=lambda x: x['start'])
        
        for slot in sorted_slots:
            if remaining_hours <= 0:
                break
                
            slot_hours = self._slot_duration(slot)
            
            # Check if this slot can accommodate at least minimum block size
            if slot_hours >= min_block_hours:
                # Use as much of this slot as needed/possible
                hours_to_use = min(remaining_hours, slot_hours)
                
                # Only use this slot if it meets minimum block size requirement
                if hours_to_use >= min_block_hours:
                    duration = timedelta(hours=hours_to_use)
                    suitable_slots.append({
                        'start': slot['start'],
                        'end': slot['start'] + duration,
                        'block_id': slot['block_id'],
                        'split_index': len(suitable_slots)  # Track which part of split task this is
                    })
                    remaining_hours -= hours_to_use
        
        # Only return slots if we can schedule at least 75% of the task
        scheduled_hours = required_hours - remaining_hours
        if scheduled_hours >= required_hours * 0.75:
            return suitable_slots
        
        return []  # Can't adequately schedule this task

    def _detect_overload_with_analysis(self, tasks: List[Task], available_slots: List[dict]) -> dict:
        """
        Enhanced overload detection with detailed analysis.
        Returns a dict with overload analysis information.
        """
        total_required_hours = sum(float(t.estimated_hours) for t in tasks)
        total_available_hours = sum(self._slot_duration(slot) for slot in available_slots)
        
        # Calculate overload severity
        overload_ratio = total_required_hours / max(total_available_hours, 0.01)  # Avoid division by zero
        
        # Analyze task distribution by priority
        priority_distribution = {}
        for task in tasks:
            priority = task.priority
            if priority not in priority_distribution:
                priority_distribution[priority] = {'count': 0, 'hours': 0}
            priority_distribution[priority]['count'] += 1
            priority_distribution[priority]['hours'] += float(task.estimated_hours)
        
        return {
            'is_overloaded': total_required_hours > total_available_hours,
            'overload_ratio': overload_ratio,
            'total_required_hours': total_required_hours,
            'total_available_hours': total_available_hours,
            'excess_hours': max(0, total_required_hours - total_available_hours),
            'priority_distribution': priority_distribution,
            'recommendations': self._generate_overload_recommendations(overload_ratio, priority_distribution)
        }

    def _generate_overload_recommendations(self, overload_ratio: float, priority_distribution: dict) -> List[str]:
        """
        Generate recommendations for handling overload scenarios.
        """
        recommendations = []
        
        if overload_ratio > 2.0:
            recommendations.append("Consider deferring low-priority tasks to next week")
            recommendations.append("Break large tasks into smaller, more manageable chunks")
        elif overload_ratio > 1.2:
            recommendations.append("Look for opportunities to reduce task scope")
            recommendations.append("Consider extending deadlines where possible")
        elif overload_ratio > 1.1:
            recommendations.append("Schedule might be tight - consider adding more availability")
        
        # Priority-specific recommendations
        if 1 in priority_distribution and priority_distribution[1]['hours'] > 8:
            recommendations.append("Many high-priority tasks detected - ensure adequate focus time")
        
        if 4 in priority_distribution and priority_distribution[4]['hours'] > 4:
            recommendations.append("Consider deferring some low-priority tasks")
        
        return recommendations

    def calculate_schedule_with_analysis(self, tasks: List[Task] = None, time_blocks: List[TimeBlock] = None) -> dict:
        """
        Enhanced scheduling function that returns detailed analysis along with scheduled tasks.
        """
        if tasks is None:
            tasks = list(self.user.tasks.filter(status__in=['todo', 'in_progress'], is_locked=False))
        
        if time_blocks is None:
            time_blocks = list(self.user.time_blocks.all())

        # Create available time slots from time blocks
        available_slots = self._generate_available_slots(time_blocks)
        
        # Analyze overload before scheduling
        overload_analysis = self._detect_overload_with_analysis(tasks, available_slots)
        
        # Separate urgent and regular tasks for proper prioritization (consistent with calculate_schedule)
        now = timezone.now()
        urgent_deadline = now + timedelta(hours=24)
        
        urgent_tasks = []
        regular_tasks = []
        
        for task in tasks:
            if (task.deadline and task.deadline <= urgent_deadline and task.deadline > now) or task.priority == 4:
                urgent_tasks.append(task)
            else:
                regular_tasks.append(task)
        
        # Sort urgent tasks by deadline (most urgent first), then regular tasks by priority
        urgent_tasks_sorted = sorted(urgent_tasks, key=lambda t: (t.deadline or now + timedelta(days=365), -t.priority))
        regular_tasks_sorted = sorted(regular_tasks, key=lambda t: self._calculate_task_priority_score(t))
        
        # Combine with urgent tasks first (consistent with calculate_schedule)
        tasks_to_schedule = urgent_tasks_sorted + regular_tasks_sorted

        scheduled_tasks = []
        unscheduled_tasks = []
        scheduling_decisions = []  # Track decisions for analysis

        if overload_analysis['is_overloaded']:
            # Use enhanced overload handling
            return self._handle_overload_with_analysis(tasks_to_schedule, available_slots, overload_analysis)

        # Enhanced scheduling with task splitting
        remaining_slots = available_slots.copy()
        
        for task in tasks_to_schedule:
            suitable_slots = self._find_suitable_slot_with_splitting(task, remaining_slots)
            
            if suitable_slots:
                # Schedule the task (possibly split across multiple slots)
                if len(suitable_slots) == 1:
                    # Single slot scheduling
                    slot = suitable_slots[0]
                    task.start_time = slot['start']
                    task.end_time = slot['end']
                    scheduled_tasks.append(task)
                    scheduling_decisions.append({
                        'task': task.title,
                        'decision': 'scheduled_single_slot',
                        'slot_count': 1,
                        'total_hours': self._slot_duration(slot)
                    })
                else:
                    # Multi-slot scheduling (task splitting)
                    # For now, schedule in the first slot and track that it's split
                    # In a more advanced implementation, you might create multiple task instances
                    first_slot = suitable_slots[0]
                    task.start_time = first_slot['start']
                    task.end_time = first_slot['end']
                    scheduled_tasks.append(task)
                    
                    total_scheduled_hours = sum(self._slot_duration(s) for s in suitable_slots)
                    scheduling_decisions.append({
                        'task': task.title,
                        'decision': 'scheduled_split',
                        'slot_count': len(suitable_slots),
                        'total_hours': total_scheduled_hours,
                        'note': 'Task split across multiple time blocks'
                    })
                
                # Update remaining slots
                for slot in suitable_slots:
                    remaining_slots = self._update_available_slots(remaining_slots, slot)
            else:
                unscheduled_tasks.append(task)
                scheduling_decisions.append({
                    'task': task.title,
                    'decision': 'unscheduled',
                    'reason': 'No suitable time slots available'
                })

        return {
            'scheduled_tasks': scheduled_tasks,
            'unscheduled_tasks': unscheduled_tasks,
            'overload_analysis': overload_analysis,
            'scheduling_decisions': scheduling_decisions,
            'total_scheduled_hours': sum(float(t.estimated_hours) for t in scheduled_tasks),
            'total_available_hours': sum(self._slot_duration(slot) for slot in available_slots),
            'utilization_rate': (sum(float(t.estimated_hours) for t in scheduled_tasks) / 
                               max(sum(self._slot_duration(slot) for slot in available_slots), 0.01)) * 100
        }

    def _handle_overload_with_analysis(self, tasks: List[Task], available_slots: List[dict], overload_analysis: dict) -> dict:
        """
        Enhanced overload handling with detailed analysis and smart task selection.
        """
        scheduled_tasks = []
        unscheduled_tasks = []
        scheduling_decisions = []
        
        remaining_slots = available_slots.copy()
        
        # In overload scenarios, prioritize tasks more aggressively
        # Focus on highest priority and most urgent tasks first
        
        for task in tasks:
            suitable_slots = self._find_suitable_slot_with_splitting(task, remaining_slots)
            
            if suitable_slots:
                # In overload, be more selective - only schedule if we can fit at least 50% of task
                total_scheduled_hours = sum(self._slot_duration(s) for s in suitable_slots)
                task_hours = float(task.estimated_hours)
                
                if total_scheduled_hours >= task_hours * 0.5:  # At least 50% of task
                    first_slot = suitable_slots[0]
                    task.start_time = first_slot['start']
                    task.end_time = first_slot['end']
                    scheduled_tasks.append(task)
                    
                    scheduling_decisions.append({
                        'task': task.title,
                        'decision': 'scheduled_overload',
                        'coverage_percent': (total_scheduled_hours / task_hours) * 100,
                        'priority': task.priority,
                        'reason': 'High priority task in overload scenario'
                    })
                    
                    # Update remaining slots
                    for slot in suitable_slots:
                        remaining_slots = self._update_available_slots(remaining_slots, slot)
                else:
                    unscheduled_tasks.append(task)
                    scheduling_decisions.append({
                        'task': task.title,
                        'decision': 'unscheduled_overload',
                        'reason': f'Insufficient time available ({total_scheduled_hours:.1f}h of {task_hours:.1f}h needed)'
                    })
            else:
                unscheduled_tasks.append(task)
                scheduling_decisions.append({
                    'task': task.title,
                    'decision': 'unscheduled_overload',
                    'reason': 'No suitable time slots in overload scenario'
                })
        
        return {
            'scheduled_tasks': scheduled_tasks,
            'unscheduled_tasks': unscheduled_tasks,
            'overload_analysis': overload_analysis,
            'scheduling_decisions': scheduling_decisions,
            'total_scheduled_hours': sum(float(t.estimated_hours) for t in scheduled_tasks),
            'total_available_hours': sum(self._slot_duration(slot) for slot in available_slots),
            'utilization_rate': (sum(float(t.estimated_hours) for t in scheduled_tasks) / 
                               max(sum(self._slot_duration(slot) for slot in available_slots), 0.01)) * 100,
            'overload_handled': True
        }
