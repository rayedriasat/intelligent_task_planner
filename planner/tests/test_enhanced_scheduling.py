"""
Tests for the enhanced scheduling engine features (Epic 2.3).
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from unittest.mock import patch

from planner.models import Task, TimeBlock
from planner.services.scheduling_engine import SchedulingEngine


class EnhancedSchedulingEngineTestCase(TestCase):
    """Test cases for the enhanced scheduling engine features."""

    def setUp(self):
        """Set up test data for each test."""
        self.user = User.objects.create_user(
            username='testuser_enhanced',
            email='test_enhanced@example.com',
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

    def create_time_block(self, start_hour=9, end_hour=17, day_offset=0):
        """Helper method to create a test time block."""
        block_date = self.mock_now.date() + timedelta(days=day_offset)
        start_time = timezone.make_aware(datetime.combine(block_date, datetime.min.time().replace(hour=start_hour)))
        end_time = timezone.make_aware(datetime.combine(block_date, datetime.min.time().replace(hour=end_hour)))
        
        return TimeBlock.objects.create(
            user=self.user,
            start_time=start_time,
            end_time=end_time,
            is_recurring=False
        )

    @patch('django.utils.timezone.now')
    def test_enhanced_priority_scoring(self, mock_timezone_now):
        """Test the enhanced priority scoring algorithm."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create tasks with different urgencies and priorities
        urgent_task = self.create_task(title="Urgent Task", priority=4, deadline_days_from_now=1)  # Due tomorrow
        high_priority_task = self.create_task(title="High Priority", priority=3, deadline_days_from_now=7)  # Due in a week
        low_priority_task = self.create_task(title="Low Priority", priority=1, deadline_days_from_now=2)  # Due in 2 days
        
        # Test priority scoring
        urgent_score = self.engine._calculate_task_priority_score(urgent_task)
        high_priority_score = self.engine._calculate_task_priority_score(high_priority_task)
        low_priority_score = self.engine._calculate_task_priority_score(low_priority_task)
        
        # Urgent task should have the lowest (best) score
        self.assertLess(urgent_score, high_priority_score)
        self.assertLess(urgent_score, low_priority_score)

    @patch('django.utils.timezone.now')
    def test_task_splitting_functionality(self, mock_timezone_now):
        """Test intelligent task splitting across multiple time slots."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create a 4-hour task
        task = self.create_task(title="Large Task", estimated_hours=4.0, min_block_size=1.0)
        
        # Create two 2-hour time blocks on the same day (both after 10 AM mock time)
        time_block1 = self.create_time_block(start_hour=11, end_hour=13, day_offset=0)  # 2 hours today 11 AM-1 PM
        time_block2 = self.create_time_block(start_hour=14, end_hour=16, day_offset=0)  # 2 hours today 2-4 PM
        
        available_slots = self.engine._generate_available_slots([time_block1, time_block2])
        suitable_slots = self.engine._find_suitable_slot_with_splitting(task, available_slots)
        
        # Should find 2 slots to split the task
        self.assertEqual(len(suitable_slots), 2)
        total_hours = sum(self.engine._slot_duration(slot) for slot in suitable_slots)
        self.assertEqual(total_hours, 4.0)

    @patch('django.utils.timezone.now')
    def test_overload_detection_and_analysis(self, mock_timezone_now):
        """Test enhanced overload detection with detailed analysis."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create tasks totaling 10 hours
        tasks = [
            self.create_task(title="Task 1", estimated_hours=3.0, priority=1),
            self.create_task(title="Task 2", estimated_hours=3.0, priority=2),
            self.create_task(title="Task 3", estimated_hours=2.0, priority=3),
            self.create_task(title="Task 4", estimated_hours=2.0, priority=4),
        ]
        
        # Create time blocks totaling only 6 hours
        time_blocks = [
            self.create_time_block(start_hour=9, end_hour=12, day_offset=0),   # 3 hours
            self.create_time_block(start_hour=14, end_hour=17, day_offset=0),  # 3 hours
        ]
        
        available_slots = self.engine._generate_available_slots(time_blocks)
        overload_analysis = self.engine._detect_overload_with_analysis(tasks, available_slots)
        
        self.assertTrue(overload_analysis['is_overloaded'])
        self.assertEqual(overload_analysis['total_required_hours'], 10.0)
        self.assertEqual(overload_analysis['total_available_hours'], 5.0)  # 10 AM to 12 PM, 2 PM to 5 PM = 5 hours
        self.assertEqual(overload_analysis['excess_hours'], 5.0)
        self.assertGreater(overload_analysis['overload_ratio'], 1.0)
        self.assertIsInstance(overload_analysis['recommendations'], list)
        self.assertGreater(len(overload_analysis['recommendations']), 0)

    @patch('django.utils.timezone.now')
    def test_calculate_schedule_with_analysis(self, mock_timezone_now):
        """Test the enhanced scheduling function that returns detailed analysis."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create moderate workload (not overloaded)
        tasks = [
            self.create_task(title="Task 1", estimated_hours=2.0, priority=1),
            self.create_task(title="Task 2", estimated_hours=1.5, priority=2),
        ]
        
        # Create sufficient time blocks
        time_block = self.create_time_block(start_hour=14, end_hour=18, day_offset=0)  # 4 hours
        
        result = self.engine.calculate_schedule_with_analysis(tasks, [time_block])
        
        # Should successfully schedule both tasks
        self.assertEqual(len(result['scheduled_tasks']), 2)
        self.assertEqual(len(result['unscheduled_tasks']), 0)
        self.assertFalse(result['overload_analysis']['is_overloaded'])
        self.assertIsInstance(result['scheduling_decisions'], list)
        self.assertGreater(result['utilization_rate'], 0)
        self.assertEqual(result['total_scheduled_hours'], 3.5)

    @patch('django.utils.timezone.now')
    def test_overload_handling_with_analysis(self, mock_timezone_now):
        """Test enhanced overload handling prioritizes correctly."""
        mock_timezone_now.return_value = self.mock_now
        
        # Create overload scenario
        tasks = [
            self.create_task(title="Low Priority", estimated_hours=2.0, priority=1, deadline_days_from_now=1),
            self.create_task(title="Medium Priority", estimated_hours=2.0, priority=2, deadline_days_from_now=3),
            self.create_task(title="Urgent Priority", estimated_hours=2.0, priority=4, deadline_days_from_now=7),
        ]
        
        # Limited time
        time_block = self.create_time_block(start_hour=14, end_hour=16, day_offset=0)  # 2 hours only
        
        result = self.engine.calculate_schedule_with_analysis(tasks, [time_block])
        
        # Should be detected as overloaded
        self.assertTrue(result['overload_analysis']['is_overloaded'])
        self.assertTrue(result.get('overload_handled', False))
        
        # Should prioritize the highest priority task
        self.assertGreater(len(result['scheduled_tasks']), 0)
        if result['scheduled_tasks']:
            self.assertEqual(result['scheduled_tasks'][0].title, "High Priority")

    @patch('django.utils.timezone.now')
    def test_scheduling_decisions_tracking(self, mock_timezone_now):
        """Test that scheduling decisions are properly tracked."""
        mock_timezone_now.return_value = self.mock_now
        
        task = self.create_task(title="Trackable Task", estimated_hours=2.0)
        time_block = self.create_time_block(start_hour=14, end_hour=16, day_offset=0)
        
        result = self.engine.calculate_schedule_with_analysis([task], [time_block])
        
        self.assertEqual(len(result['scheduling_decisions']), 1)
        decision = result['scheduling_decisions'][0]
        self.assertEqual(decision['task'], "Trackable Task")
        self.assertIn(decision['decision'], ['scheduled_single_slot', 'scheduled_split'])

    @patch('django.utils.timezone.now')
    def test_utilization_rate_calculation(self, mock_timezone_now):
        """Test that utilization rate is calculated correctly."""
        mock_timezone_now.return_value = self.mock_now
        
        # 2-hour task in 4-hour time block = 50% utilization
        task = self.create_task(title="Half Utilization", estimated_hours=2.0)
        time_block = self.create_time_block(start_hour=14, end_hour=18, day_offset=0)  # 4 hours
        
        result = self.engine.calculate_schedule_with_analysis([task], [time_block])
        
        expected_utilization = (2.0 / 4.0) * 100  # 4 hours available (2 PM to 6 PM), 2 hours used = 50%
        self.assertAlmostEqual(result['utilization_rate'], expected_utilization, places=1)

    def test_overload_recommendations_generation(self):
        """Test that appropriate recommendations are generated for different overload scenarios."""
        # Test severe overload
        severe_recommendations = self.engine._generate_overload_recommendations(
            overload_ratio=2.5, 
            priority_distribution={1: {'count': 3, 'hours': 10}}
        )
        
        self.assertIn("Consider deferring low-priority tasks to next week", severe_recommendations)
        self.assertIn("Many high-priority tasks detected - ensure adequate focus time", severe_recommendations)
        
        # Test moderate overload
        moderate_recommendations = self.engine._generate_overload_recommendations(
            overload_ratio=1.3, 
            priority_distribution={4: {'count': 2, 'hours': 6}}
        )
        
        self.assertIn("Look for opportunities to reduce task scope", moderate_recommendations)
        self.assertIn("Consider deferring some low-priority tasks", moderate_recommendations)