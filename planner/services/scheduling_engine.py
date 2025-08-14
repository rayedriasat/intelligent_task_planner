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

    def calculate_schedule(self, tasks: List[Task] = None, time_blocks: List[TimeBlock] = None) -> Tuple[List[Task], List[Task]]:
        """
        Main scheduling function that takes tasks and time blocks,
        returns scheduled and unscheduled tasks.
        """
        if tasks is None:
            tasks = list(self.user.tasks.filter(status__in=['todo', 'in_progress'], is_locked=False))
        
        if time_blocks is None:
            time_blocks = list(self.user.time_blocks.all())

        # Create available time slots from time blocks
        available_slots = self._generate_available_slots(time_blocks)
        
        # Sort tasks by priority and deadline
        tasks_to_schedule = sorted(
            tasks,
            key=lambda t: (t.priority, t.deadline)
        )

        scheduled_tasks = []
        unscheduled_tasks = []

        # Check for overload before scheduling
        total_required_hours = sum(t.estimated_hours for t in tasks_to_schedule)
        total_available_hours = sum(self._slot_duration(slot) for slot in available_slots)

        if total_required_hours > total_available_hours:
            # Handle overload scenario
            return self._handle_overload(tasks_to_schedule, available_slots)

        # Schedule tasks
        for task in tasks_to_schedule:
            scheduled_slot = self._find_suitable_slot(task, available_slots)
            
            if scheduled_slot:
                # Schedule the task
                task.start_time = scheduled_slot['start']
                task.end_time = scheduled_slot['end']
                scheduled_tasks.append(task)
                
                # Remove or split the used slot
                available_slots = self._update_available_slots(available_slots, scheduled_slot)
            else:
                unscheduled_tasks.append(task)

        return scheduled_tasks, unscheduled_tasks

    def _generate_available_slots(self, time_blocks: List[TimeBlock]) -> List[dict]:
        """Generate available time slots from time blocks for the current week."""
        now = timezone.now()
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=7)
        
        slots = []
        
        for block in time_blocks:
            if block.is_recurring:
                # Generate slots for the week based on day_of_week
                for day in range(7):
                    if day == block.day_of_week:
                        slot_date = week_start + timedelta(days=day)
                        slot_start = slot_date.replace(
                            hour=block.start_time.hour,
                            minute=block.start_time.minute,
                            second=0,
                            microsecond=0
                        )
                        slot_end = slot_date.replace(
                            hour=block.end_time.hour,
                            minute=block.end_time.minute,
                            second=0,
                            microsecond=0
                        )
                        
                        if slot_start >= now:  # Only future slots
                            slots.append({
                                'start': slot_start,
                                'end': slot_end,
                                'block_id': block.id
                            })
            else:
                # Single occurrence
                if block.start_time >= now and block.start_time <= week_end:
                    slots.append({
                        'start': block.start_time,
                        'end': block.end_time,
                        'block_id': block.id
                    })

        # Remove conflicts with existing scheduled tasks
        scheduled_tasks = self.user.tasks.filter(
            start_time__isnull=False,
            end_time__isnull=False,
            status__in=['todo', 'in_progress']
        )
        
        for task in scheduled_tasks:
            if task.is_locked:
                slots = self._remove_conflicts(slots, task.start_time, task.end_time)

        return sorted(slots, key=lambda x: x['start'])

    def _find_suitable_slot(self, task: Task, available_slots: List[dict]) -> Optional[dict]:
        """Find a suitable time slot for the given task."""
        
        # Convert Decimal to float for timedelta
        required_duration = timedelta(hours=float(task.estimated_hours))
        min_duration = timedelta(hours=float(task.min_block_size))
        
        for slot in available_slots:
            slot_duration = slot['end'] - slot['start']
            
            # Check if slot is big enough for minimum block size
            if slot_duration >= min_duration:
                # Check if we can fit the full task
                if slot_duration >= required_duration:
                    # Schedule for the full duration
                    return {
                        'start': slot['start'],
                        'end': slot['start'] + required_duration,
                        'block_id': slot['block_id']
                    }
                else:
                    # Can fit minimum block but not full task
                    # Schedule what we can fit
                    return {
                        'start': slot['start'],
                        'end': slot['end'],
                        'block_id': slot['block_id']
                    }
        
        return None

    def _update_available_slots(self, slots: List[dict], used_slot: dict) -> List[dict]:
        """Update available slots after scheduling a task."""
        updated_slots = []
        
        for slot in slots:
            if slot['block_id'] == used_slot['block_id']:
                # This is the slot we used
                if slot['start'] < used_slot['start']:
                    # There's time before the used slot
                    updated_slots.append({
                        'start': slot['start'],
                        'end': used_slot['start'],
                        'block_id': slot['block_id']
                    })
                
                if used_slot['end'] < slot['end']:
                    # There's time after the used slot
                    updated_slots.append({
                        'start': used_slot['end'],
                        'end': slot['end'],
                        'block_id': slot['block_id']
                    })
            else:
                # Keep other slots as is
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
        
        # Recalculate schedule
        return self.calculate_schedule()
