"""
Comprehensive unit tests for the SchedulingEngine.
These tests validate the core scheduling logic as required by Epic 1.5.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from unittest.mock import patch, MagicMock

from planner.models import Task, TimeBlock
from planner.services.scheduling_engine import SchedulingEngine


class SchedulingEngineTestCase(TestCase):
    """Test cases for the SchedulingEngine class."""

    def setUp(self):
        """Set up test data for each test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.engine = SchedulingEngine(self.user)
        
        # Create a fixed "now" for consistent testing
        self.mock_now = timezone.make_aware(
            datetime(2024, 1, 1, 10, 0, 0)  # Monday 10:00 AM
        )

    def create_task(self, title="Test Task", estimated_hours=2.0, min_block_size=0.5, 
                   priority=2, deadline_days_from_now=7, status='todo'):
        """Helper method to create a test task."""
        deadline = self.mock_now + timedelta(days=deadline_days_from_now)
        return Task.objects.create(
            user=self.user,
            title=title,
            estimated_hours=Decimal(str(estimated_hours)),
            min_block_size=Decimal(str(min_block_size)),
            priority=priority,
            deadline=deadline,
            status=status
        )

    def create_time_block(self, start_hour=9, end_hour=17, day_offset=0, is_recurring=False, day_of_week=None):
        """Helper method to create a test time block."""
        if is_recurring and day_of_week is not None:
            # For recurring blocks, use a base time for the start/end times
            base_date = timezone.now().date()
            start_time = timezone.make_aware(datetime.combine(base_date, datetime.min.time().replace(hour=start_hour)))
            end_time = timezone.make_aware(datetime.combine(base_date, datetime.min.time().replace(hour=end_hour)))
        else:
            # For non-recurring blocks, use the actual date
            block_date = self.mock_now.date() + timedelta(days=day_offset)
            start_time = timezone.make_aware(datetime.combine(block_date, datetime.min.time().replace(hour=start_hour)))
            end_time = timezone.make_aware(datetime.combine(block_date, datetime.min.time().replace(hour=end_hour)))
        
        return TimeBlock.objects.create(
            user=self.user,
            start_time=start_time,
            end_time=end_time,
            is_recurring=is_recurring,
            day_of_week=day_of_week
        )

    @patch('django.utils.timezone.now')
    def test_calculate_schedule_single_task_perfect_fit(self, mock_timezone_now):
        """Test scheduling a single task that fits perfectly in available time."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create a 2-hour task
        task = self.create_task(estimated_hours=2.0)
        
        # Create a 2-hour time block today from 2 PM to 4 PM
        time_block = self.create_time_block(start_hour=14, end_hour=16, day_offset=0)
        
        scheduled_tasks, unscheduled_tasks = self.engine.calculate_schedule([task], [time_block])
        
        self.assertEqual(len(scheduled_tasks), 1)
        self.assertEqual(len(unscheduled_tasks), 0)
        self.assertEqual(scheduled_tasks[0].title, "Test Task")
        self.assertIsNotNone(scheduled_tasks[0].start_time)
        self.assertIsNotNone(scheduled_tasks[0].end_time)
        
        # Check that the task is scheduled within the time block
        self.assertEqual(scheduled_tasks[0].start_time.hour, 14)
        self.assertEqual(scheduled_tasks[0].end_time.hour, 16)

    @patch('django.utils.timezone.now')
    def test_calculate_schedule_no_available_time(self, mock_timezone_now):
        """Test scheduling when no time blocks are available."""
        mock_timezone_now.return_value = self.mock_now
        
        task = self.create_task(estimated_hours=2.0)
        
        scheduled_tasks, unscheduled_tasks = self.engine.calculate_schedule([task], [])
        
        self.assertEqual(len(scheduled_tasks), 0)
        self.assertEqual(len(unscheduled_tasks), 1)
        self.assertEqual(unscheduled_tasks[0].title, "Test Task")

    @patch('django.utils.timezone.now')
    def test_calculate_schedule_task_too_large_for_available_time(self, mock_timezone_now):
        """Test scheduling a task that's larger than available time."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create a 4-hour task
        task = self.create_task(estimated_hours=4.0, min_block_size=1.0)
        
        # Create a 2-hour time block
        time_block = self.create_time_block(start_hour=14, end_hour=16, day_offset=0)
        
        scheduled_tasks, unscheduled_tasks = self.engine.calculate_schedule([task], [time_block])
        
        # Task should be partially scheduled (2 hours instead of 4)
        self.assertEqual(len(scheduled_tasks), 1)
        self.assertEqual(len(unscheduled_tasks), 0)
        
        # Check that it's scheduled for the available time
        duration = scheduled_tasks[0].end_time - scheduled_tasks[0].start_time
        self.assertEqual(duration.total_seconds() / 3600, 2.0)  # 2 hours

    @patch('django.utils.timezone.now')
    def test_calculate_schedule_task_smaller_than_min_block_size(self, mock_timezone_now):
        """Test that tasks smaller than min_block_size are not scheduled."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create a task that needs 2 hours but min block size is 3 hours
        task = self.create_task(estimated_hours=2.0, min_block_size=3.0)
        
        # Create a 2-hour time block
        time_block = self.create_time_block(start_hour=14, end_hour=16, day_offset=0)
        
        scheduled_tasks, unscheduled_tasks = self.engine.calculate_schedule([task], [time_block])
        
        self.assertEqual(len(scheduled_tasks), 0)
        self.assertEqual(len(unscheduled_tasks), 1)

    @patch('django.utils.timezone.now')
    def test_calculate_schedule_multiple_tasks_priority_ordering(self, mock_timezone_now):
        """Test that tasks are scheduled in priority order."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create tasks with different priorities
        low_priority_task = self.create_task(title="Low Priority", priority=1, estimated_hours=1.0)
        high_priority_task = self.create_task(title="High Priority", priority=4, estimated_hours=1.0)
        medium_priority_task = self.create_task(title="Medium Priority", priority=2, estimated_hours=1.0)
        
        # Create a time block that can fit only 2 tasks
        time_block = self.create_time_block(start_hour=14, end_hour=16, day_offset=0)  # 2 hours
        
        tasks = [low_priority_task, high_priority_task, medium_priority_task]
        scheduled_tasks, unscheduled_tasks = self.engine.calculate_schedule(tasks, [time_block])
        
        self.assertEqual(len(scheduled_tasks), 2)
        self.assertEqual(len(unscheduled_tasks), 1)
        
        # High priority task should be scheduled first (priority 4 = Urgent is highest priority)
        self.assertEqual(scheduled_tasks[0].title, "High Priority")  # Priority 4 (Urgent) comes first
        self.assertEqual(scheduled_tasks[1].title, "Medium Priority")  # Priority 2 (Medium) comes second
        self.assertEqual(unscheduled_tasks[0].title, "Low Priority")  # Priority 1 (Low) doesn't fit

    @patch('django.utils.timezone.now')
    def test_calculate_schedule_overload_scenario(self, mock_timezone_now):
        """Test overload handling when total task time exceeds available time."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create tasks totaling 6 hours
        task1 = self.create_task(title="Task 1", estimated_hours=2.0, priority=1)
        task2 = self.create_task(title="Task 2", estimated_hours=2.0, priority=2)
        task3 = self.create_task(title="Task 3", estimated_hours=2.0, priority=3)
        
        # Create time blocks totaling only 4 hours
        time_block1 = self.create_time_block(start_hour=9, end_hour=11, day_offset=0)   # 2 hours
        time_block2 = self.create_time_block(start_hour=14, end_hour=16, day_offset=0)  # 2 hours
        
        tasks = [task1, task2, task3]
        time_blocks = [time_block1, time_block2]
        scheduled_tasks, unscheduled_tasks = self.engine.calculate_schedule(tasks, time_blocks)
        
        # Should schedule highest priority tasks first
        self.assertEqual(len(scheduled_tasks), 2)
        self.assertEqual(len(unscheduled_tasks), 1)
        self.assertEqual(scheduled_tasks[0].title, "Task 1")
        self.assertEqual(scheduled_tasks[1].title, "Task 2")
        self.assertEqual(unscheduled_tasks[0].title, "Task 3")

    @patch('django.utils.timezone.now')
    def test_calculate_schedule_with_existing_locked_tasks(self, mock_timezone_now):
        """Test that locked tasks create conflicts and reduce available time."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create a time block from 9 AM to 5 PM
        time_block = self.create_time_block(start_hour=9, end_hour=17, day_offset=0)
        
        # Create an existing locked task from 1 PM to 3 PM
        locked_task = self.create_task(title="Locked Task", estimated_hours=2.0)
        locked_task.start_time = self.mock_now.replace(hour=13)
        locked_task.end_time = self.mock_now.replace(hour=15)
        locked_task.is_locked = True
        locked_task.save()
        
        # Create a new task to schedule
        new_task = self.create_task(title="New Task", estimated_hours=2.0)
        
        scheduled_tasks, unscheduled_tasks = self.engine.calculate_schedule([new_task], [time_block])
        
        # New task should be scheduled but not during the locked task's time
        self.assertEqual(len(scheduled_tasks), 1)
        self.assertEqual(len(unscheduled_tasks), 0)
        
        # Verify it's not scheduled during the conflict period (1 PM - 3 PM)
        scheduled_task = scheduled_tasks[0]
        conflict_start = self.mock_now.replace(hour=13)
        conflict_end = self.mock_now.replace(hour=15)
        
        # Task should either end before conflict or start after conflict
        self.assertTrue(
            scheduled_task.end_time <= conflict_start or 
            scheduled_task.start_time >= conflict_end
        )

    @patch('django.utils.timezone.now')
    def test_calculate_schedule_recurring_time_blocks(self, mock_timezone_now):
        """Test scheduling with recurring time blocks."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create a recurring time block for Monday (day 0) from 9 AM to 5 PM
        recurring_block = self.create_time_block(
            start_hour=9, end_hour=17, 
            is_recurring=True, day_of_week=0  # Monday
        )
        
        # Create a task
        task = self.create_task(estimated_hours=2.0)
        
        scheduled_tasks, unscheduled_tasks = self.engine.calculate_schedule([task], [recurring_block])
        
        self.assertEqual(len(scheduled_tasks), 1)
        self.assertEqual(len(unscheduled_tasks), 0)

    @patch('django.utils.timezone.now')
    def test_calculate_schedule_past_time_blocks_ignored(self, mock_timezone_now):
        """Test that time blocks in the past are ignored."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create a time block yesterday
        past_time_block = self.create_time_block(start_hour=9, end_hour=17, day_offset=-1)
        
        # Create a task
        task = self.create_task(estimated_hours=2.0)
        
        scheduled_tasks, unscheduled_tasks = self.engine.calculate_schedule([task], [past_time_block])
        
        # Task should not be scheduled since the time block is in the past
        self.assertEqual(len(scheduled_tasks), 0)
        self.assertEqual(len(unscheduled_tasks), 1)

    def test_slot_duration_calculation(self):
        """Test the _slot_duration helper method."""
        slot = {
            'start': timezone.make_aware(datetime(2024, 1, 1, 9, 0)),
            'end': timezone.make_aware(datetime(2024, 1, 1, 11, 30))
        }
        
        duration = self.engine._slot_duration(slot)
        self.assertEqual(duration, 2.5)  # 2.5 hours

    @patch('django.utils.timezone.now')
    def test_reschedule_week_clears_unlocked_tasks(self, mock_timezone_now):
        """Test that reschedule_week clears start/end times for unlocked tasks."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create tasks - one locked, one unlocked
        unlocked_task = self.create_task(title="Unlocked Task")
        unlocked_task.start_time = self.mock_now
        unlocked_task.end_time = self.mock_now + timedelta(hours=2)
        unlocked_task.is_locked = False
        unlocked_task.save()
        
        locked_task = self.create_task(title="Locked Task")
        locked_task.start_time = self.mock_now + timedelta(hours=3)
        locked_task.end_time = self.mock_now + timedelta(hours=5)
        locked_task.is_locked = True
        locked_task.save()
        
        # Create time blocks for rescheduling
        time_block = self.create_time_block(start_hour=9, end_hour=17, day_offset=1)
        
        self.engine.reschedule_week()
        
        # Refresh from database
        unlocked_task.refresh_from_db()
        locked_task.refresh_from_db()
        
        # Unlocked task should have its schedule cleared
        self.assertIsNone(unlocked_task.start_time)
        self.assertIsNone(unlocked_task.end_time)
        
        # Locked task should keep its schedule
        self.assertIsNotNone(locked_task.start_time)
        self.assertIsNotNone(locked_task.end_time)

    @patch('django.utils.timezone.now')
    def test_generate_available_slots_excludes_completed_tasks(self, mock_timezone_now):
        """Test that completed tasks don't affect available slots."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create a time block
        time_block = self.create_time_block(start_hour=9, end_hour=17, day_offset=0)
        
        # Create a completed task (should not affect scheduling)
        completed_task = self.create_task(title="Completed Task", status='completed')
        completed_task.start_time = self.mock_now.replace(hour=13)
        completed_task.end_time = self.mock_now.replace(hour=15)
        completed_task.is_locked = True
        completed_task.save()
        
        # Generate slots
        slots = self.engine._generate_available_slots([time_block])
        
        # Should have 7 hours available (10 AM to 5 PM, since time block started at 9 AM but now is 10 AM)
        total_hours = sum(self.engine._slot_duration(slot) for slot in slots)
        self.assertEqual(total_hours, 7.0)

    def test_update_available_slots_splits_correctly(self):
        """Test that _update_available_slots correctly splits time blocks."""
        # Create a 4-hour slot from 9 AM to 1 PM
        slot = {
            'start': timezone.make_aware(datetime(2024, 1, 1, 9, 0)),
            'end': timezone.make_aware(datetime(2024, 1, 1, 13, 0)),
            'block_id': 1
        }
        
        # Use 2 hours in the middle (10 AM to 12 PM)
        used_slot = {
            'start': timezone.make_aware(datetime(2024, 1, 1, 10, 0)),
            'end': timezone.make_aware(datetime(2024, 1, 1, 12, 0)),
            'block_id': 1
        }
        
        updated_slots = self.engine._update_available_slots([slot], used_slot)
        
        # Should result in two slots: 9-10 AM and 12-1 PM
        self.assertEqual(len(updated_slots), 2)
        
        # Check first slot (9-10 AM)
        self.assertEqual(updated_slots[0]['start'].hour, 9)
        self.assertEqual(updated_slots[0]['end'].hour, 10)
        
        # Check second slot (12-1 PM)
        self.assertEqual(updated_slots[1]['start'].hour, 12)
        self.assertEqual(updated_slots[1]['end'].hour, 13)

    def test_remove_conflicts_handles_overlaps(self):
        """Test that _remove_conflicts correctly handles various overlap scenarios."""
        # Create test slots
        slots = [
            {
                'start': timezone.make_aware(datetime(2024, 1, 1, 9, 0)),
                'end': timezone.make_aware(datetime(2024, 1, 1, 12, 0)),
                'block_id': 1
            },
            {
                'start': timezone.make_aware(datetime(2024, 1, 1, 14, 0)),
                'end': timezone.make_aware(datetime(2024, 1, 1, 17, 0)),
                'block_id': 2
            }
        ]
        
        # Conflict from 10 AM to 11 AM (overlaps first slot)
        conflict_start = timezone.make_aware(datetime(2024, 1, 1, 10, 0))
        conflict_end = timezone.make_aware(datetime(2024, 1, 1, 11, 0))
        
        updated_slots = self.engine._remove_conflicts(slots, conflict_start, conflict_end)
        
        # Should have 3 slots: 9-10 AM, 11 AM-12 PM, and 2-5 PM
        self.assertEqual(len(updated_slots), 3)
        
        # First slot should be 9-10 AM
        self.assertEqual(updated_slots[0]['start'].hour, 9)
        self.assertEqual(updated_slots[0]['end'].hour, 10)
        
        # Second slot should be 11 AM-12 PM
        self.assertEqual(updated_slots[1]['start'].hour, 11)
        self.assertEqual(updated_slots[1]['end'].hour, 12)
        
        # Third slot should be unchanged (2-5 PM)
        self.assertEqual(updated_slots[2]['start'].hour, 14)
        self.assertEqual(updated_slots[2]['end'].hour, 17)

    @patch('django.utils.timezone.now')
    def test_calculate_schedule_empty_inputs(self, mock_timezone_now):
        """Test that empty inputs are handled gracefully."""
        mock_timezone_now.return_value = self.mock_now
        
        # Test with empty tasks and time blocks
        scheduled_tasks, unscheduled_tasks = self.engine.calculate_schedule([], [])
        
        self.assertEqual(len(scheduled_tasks), 0)
        self.assertEqual(len(unscheduled_tasks), 0)
        
        # Test with tasks but no time blocks
        task = self.create_task()
        scheduled_tasks, unscheduled_tasks = self.engine.calculate_schedule([task], [])
        
        self.assertEqual(len(scheduled_tasks), 0)
        self.assertEqual(len(unscheduled_tasks), 1)

    @patch('django.utils.timezone.now')
    def test_calculate_schedule_default_parameters(self, mock_timezone_now):
        """Test that default parameters work correctly."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create some tasks and time blocks in the database
        task = self.create_task()
        time_block = self.create_time_block(start_hour=14, end_hour=16, day_offset=0)
        
        # Call without parameters (should use defaults)
        scheduled_tasks, unscheduled_tasks = self.engine.calculate_schedule()
        
        # Should find and schedule the task
        self.assertEqual(len(scheduled_tasks), 1)
        self.assertEqual(len(unscheduled_tasks), 0)