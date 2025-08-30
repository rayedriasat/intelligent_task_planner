"""
Unit tests for OpenRouter AI Integration Service

Tests cover all aspects of the AI service including:
- API call formatting
- Success scenarios
- Error handling 
- Response parsing
- Edge cases

Author: TaskFlow Team
"""

import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

# Import the service and related classes
from planner.services.ai_service import (
    OpenRouterService, 
    AIResponse, 
    AIScheduleSuggestion,
    OpenRouterAPIError,
    get_ai_scheduling_suggestions_sync
)
from planner.models import Task, TimeBlock


class TestOpenRouterService(TestCase):
    """Test cases for OpenRouter AI service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = OpenRouterService()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test tasks
        self.task1 = Task.objects.create(
            user=self.user,
            title="Complete project proposal",
            description="Write the Q4 project proposal document",
            estimated_hours=3.0,
            priority=1,
            deadline=timezone.now() + timedelta(days=2),
            status='todo'
        )
        
        self.task2 = Task.objects.create(
            user=self.user,
            title="Review code changes",
            description="Review pull requests from team",
            estimated_hours=1.5,
            priority=2,
            deadline=timezone.now() + timedelta(days=1),
            status='todo'
        )
        
        # Create test time blocks
        tomorrow = timezone.now() + timedelta(days=1)
        self.time_block1 = TimeBlock.objects.create(
            user=self.user,
            start_time=tomorrow.replace(hour=9, minute=0, second=0, microsecond=0),
            end_time=tomorrow.replace(hour=12, minute=0, second=0, microsecond=0),
            is_recurring=False
        )
        
        self.time_block2 = TimeBlock.objects.create(
            user=self.user,
            start_time=tomorrow.replace(hour=14, minute=0, second=0, microsecond=0),
            end_time=tomorrow.replace(hour=17, minute=0, second=0, microsecond=0),
            is_recurring=False
        )
    
    def test_format_tasks_for_ai(self):
        """Test task formatting for AI API."""
        tasks = [self.task1, self.task2]
        formatted = self.service.format_tasks_for_ai(tasks)
        
        self.assertEqual(len(formatted), 2)
        
        # Check first task
        task1_data = formatted[0]
        self.assertEqual(task1_data['id'], self.task1.id)
        self.assertEqual(task1_data['title'], "Complete project proposal")
        self.assertEqual(task1_data['estimated_hours'], 3.0)
        self.assertEqual(task1_data['priority'], 1)
        self.assertEqual(task1_data['status'], 'todo')
        self.assertIsNotNone(task1_data['deadline'])
        
        # Check second task
        task2_data = formatted[1]
        self.assertEqual(task2_data['id'], self.task2.id)
        self.assertEqual(task2_data['title'], "Review code changes")
        self.assertEqual(task2_data['estimated_hours'], 1.5)
        self.assertEqual(task2_data['priority'], 2)
    
    def test_format_time_blocks_for_ai(self):
        """Test time block formatting for AI API."""
        blocks = [self.time_block1, self.time_block2]
        formatted = self.service.format_time_blocks_for_ai(blocks)
        
        self.assertEqual(len(formatted), 2)
        
        # Check first block
        block1_data = formatted[0]
        self.assertEqual(block1_data['id'], self.time_block1.id)
        self.assertIsNotNone(block1_data['start_time'])
        self.assertIsNotNone(block1_data['end_time'])
        self.assertEqual(block1_data['is_recurring'], False)
    
    def test_create_ai_prompt(self):
        """Test AI prompt creation."""
        tasks = [{'id': 1, 'title': 'Test Task', 'priority': 1}]
        blocks = [{'id': 1, 'start_time': '2024-01-15T09:00:00'}]
        
        prompt = self.service.create_ai_prompt(tasks, blocks)
        
        self.assertIn("You are an expert task scheduling assistant", prompt)
        self.assertIn("TASKS TO SCHEDULE:", prompt)
        self.assertIn("AVAILABLE TIME BLOCKS:", prompt)
        self.assertIn("RESPONSE FORMAT (JSON):", prompt)
        self.assertIn("Test Task", prompt)
    
    @patch('planner.services.ai_service.httpx.AsyncClient')
    async def test_call_openrouter_api_success(self, mock_client):
        """Test successful API call to OpenRouter."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "success": True,
                            "suggestions": [
                                {
                                    "task_id": 1,
                                    "suggested_start_time": "2024-01-15T09:00:00",
                                    "suggested_end_time": "2024-01-15T12:00:00",
                                    "confidence_score": 0.95,
                                    "reasoning": "High priority task"
                                }
                            ],
                            "overall_score": 0.9,
                            "reasoning": "Optimal schedule"
                        })
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Set API key for test
        with patch.object(self.service, 'api_key', 'test-api-key'):
            result = await self.service.call_openrouter_api("test prompt")
        
        self.assertIn("choices", result)
        mock_client_instance.post.assert_called_once()
    
    @patch('planner.services.ai_service.httpx.AsyncClient')
    async def test_call_openrouter_api_timeout(self, mock_client):
        """Test API timeout handling."""
        import httpx
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        with patch.object(self.service, 'api_key', 'test-api-key'):
            with self.assertRaises(OpenRouterAPIError) as context:
                await self.service.call_openrouter_api("test prompt")
        
        self.assertIn("timed out", str(context.exception))
    
    @patch('planner.services.ai_service.httpx.AsyncClient')
    async def test_call_openrouter_api_http_error(self, mock_client):
        """Test HTTP error handling."""
        import httpx
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(
            side_effect=httpx.HTTPStatusError("401", request=Mock(), response=mock_response)
        )
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        with patch.object(self.service, 'api_key', 'test-api-key'):
            with self.assertRaises(OpenRouterAPIError) as context:
                await self.service.call_openrouter_api("test prompt")
        
        self.assertIn("HTTP 401", str(context.exception))
    
    def test_call_openrouter_api_no_key(self):
        """Test API call without API key."""
        with patch.object(self.service, 'api_key', ''):
            with self.assertRaises(OpenRouterAPIError) as context:
                import asyncio
                asyncio.run(self.service.call_openrouter_api("test prompt"))
        
        self.assertIn("API key not configured", str(context.exception))
    
    def test_parse_ai_response_success(self):
        """Test parsing successful AI response."""
        api_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "success": True,
                            "suggestions": [
                                {
                                    "task_id": 1,
                                    "suggested_start_time": "2024-01-15T09:00:00",
                                    "suggested_end_time": "2024-01-15T12:00:00",
                                    "confidence_score": 0.95,
                                    "reasoning": "High priority task scheduled optimally"
                                },
                                {
                                    "task_id": 2,
                                    "suggested_start_time": "2024-01-15T14:00:00",
                                    "suggested_end_time": "2024-01-15T15:30:00",
                                    "confidence_score": 0.8,
                                    "reasoning": "Fits well in afternoon slot"
                                }
                            ],
                            "overall_score": 0.87,
                            "reasoning": "Good schedule with minimal conflicts"
                        })
                    }
                }
            ]
        }
        
        result = self.service.parse_ai_response(api_response)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.suggestions), 2)
        self.assertEqual(result.overall_score, 0.87)
        self.assertIn("Good schedule", result.reasoning)
        
        # Check first suggestion
        suggestion1 = result.suggestions[0]
        self.assertEqual(suggestion1.task_id, 1)
        self.assertEqual(suggestion1.confidence_score, 0.95)
        self.assertIn("High priority", suggestion1.reasoning)
    
    def test_parse_ai_response_failure(self):
        """Test parsing AI response indicating failure."""
        api_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "success": False,
                            "error": "Insufficient time blocks for all tasks"
                        })
                    }
                }
            ]
        }
        
        result = self.service.parse_ai_response(api_response)
        
        self.assertFalse(result.success)
        self.assertEqual(len(result.suggestions), 0)
        self.assertIn("Insufficient time", result.error_message)
    
    def test_parse_ai_response_invalid_json(self):
        """Test parsing response with invalid JSON."""
        api_response = {
            "choices": [
                {
                    "message": {
                        "content": "This is not valid JSON"
                    }
                }
            ]
        }
        
        result = self.service.parse_ai_response(api_response)
        
        self.assertFalse(result.success)
        self.assertIn("JSON parse error", result.error_message)
    
    def test_parse_ai_response_missing_choices(self):
        """Test parsing response with missing choices."""
        api_response = {"usage": {"tokens": 100}}
        
        result = self.service.parse_ai_response(api_response)
        
        self.assertFalse(result.success)
        self.assertIn("Invalid API response format", result.error_message)
    
    @patch.object(OpenRouterService, 'call_openrouter_api')
    async def test_get_scheduling_suggestions_success(self, mock_api_call):
        """Test successful end-to-end scheduling suggestions."""
        # Mock API response
        mock_api_call.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "success": True,
                            "suggestions": [
                                {
                                    "task_id": self.task1.id,
                                    "suggested_start_time": "2024-01-15T09:00:00",
                                    "suggested_end_time": "2024-01-15T12:00:00",
                                    "confidence_score": 0.95,
                                    "reasoning": "Perfect fit for morning slot"
                                }
                            ],
                            "overall_score": 0.9,
                            "reasoning": "Excellent schedule optimization"
                        })
                    }
                }
            ]
        }
        
        with patch.object(self.service, 'api_key', 'test-api-key'):
            result = await self.service.get_scheduling_suggestions(
                [self.task1], [self.time_block1]
            )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.suggestions), 1)
        self.assertEqual(result.suggestions[0].task_id, self.task1.id)
        self.assertEqual(result.overall_score, 0.9)
    
    async def test_get_scheduling_suggestions_no_tasks(self):
        """Test with no tasks provided."""
        result = await self.service.get_scheduling_suggestions([], [self.time_block1])
        
        self.assertFalse(result.success)
        self.assertIn("No tasks provided", result.error_message)
    
    async def test_get_scheduling_suggestions_no_time_blocks(self):
        """Test with no time blocks available."""
        result = await self.service.get_scheduling_suggestions([self.task1], [])
        
        self.assertFalse(result.success)
        self.assertIn("No available time blocks", result.error_message)
    
    @patch.object(OpenRouterService, 'call_openrouter_api')
    async def test_get_scheduling_suggestions_api_error(self, mock_api_call):
        """Test handling of API errors."""
        mock_api_call.side_effect = OpenRouterAPIError("API key invalid")
        
        with patch.object(self.service, 'api_key', 'invalid-key'):
            result = await self.service.get_scheduling_suggestions(
                [self.task1], [self.time_block1]
            )
        
        self.assertFalse(result.success)
        self.assertIn("API key invalid", result.error_message)
        self.assertEqual(result.reasoning, "API communication failed")


class TestSyncWrapper(TestCase):
    """Test the synchronous wrapper function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='syncuser',
            email='sync@example.com',
            password='testpass123'
        )
        
        self.task = Task.objects.create(
            user=self.user,
            title="Sync test task",
            estimated_hours=2.0,
            priority=1,
            status='todo'
        )
        
        tomorrow = timezone.now() + timedelta(days=1)
        self.time_block = TimeBlock.objects.create(
            user=self.user,
            start_time=tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
            end_time=tomorrow.replace(hour=12, minute=0, second=0, microsecond=0),
            is_recurring=False
        )
    
    @patch.object(OpenRouterService, 'get_scheduling_suggestions')
    def test_sync_wrapper_success(self, mock_async_method):
        """Test successful synchronous wrapper call."""
        # Mock async method
        mock_response = AIResponse(
            success=True,
            suggestions=[
                AIScheduleSuggestion(
                    task_id=self.task.id,
                    suggested_start_time="2024-01-15T10:00:00",
                    suggested_end_time="2024-01-15T12:00:00",
                    confidence_score=0.9,
                    reasoning="Perfect fit"
                )
            ],
            overall_score=0.9,
            reasoning="Great schedule"
        )
        
        async def mock_async_func(*args, **kwargs):
            return mock_response
        
        mock_async_method.return_value = mock_async_func()
        
        with patch('planner.services.ai_service.settings.OPENROUTER_API_KEY', 'test-key'):
            result = get_ai_scheduling_suggestions_sync([self.task], [self.time_block])
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.suggestions), 1)
        self.assertEqual(result.overall_score, 0.9)
    
    def test_sync_wrapper_exception(self):
        """Test synchronous wrapper exception handling."""
        with patch('asyncio.new_event_loop', side_effect=Exception("Event loop error")):
            result = get_ai_scheduling_suggestions_sync([self.task], [self.time_block])
        
        self.assertFalse(result.success)
        self.assertIn("Event loop error", result.error_message)


class TestDataClasses(TestCase):
    """Test the data classes and structures."""
    
    def test_ai_schedule_suggestion(self):
        """Test AIScheduleSuggestion data class."""
        suggestion = AIScheduleSuggestion(
            task_id=123,
            suggested_start_time="2024-01-15T09:00:00",
            suggested_end_time="2024-01-15T10:00:00",
            confidence_score=0.85,
            reasoning="Good time slot"
        )
        
        self.assertEqual(suggestion.task_id, 123)
        self.assertEqual(suggestion.confidence_score, 0.85)
        self.assertIn("Good time", suggestion.reasoning)
    
    def test_ai_response(self):
        """Test AIResponse data class."""
        response = AIResponse(
            success=True,
            suggestions=[],
            overall_score=0.75,
            reasoning="Decent optimization",
            error_message=None
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.overall_score, 0.75)
        self.assertIsNone(response.error_message)
    
    def test_ai_response_with_error(self):
        """Test AIResponse with error."""
        response = AIResponse(
            success=False,
            suggestions=[],
            overall_score=0.0,
            reasoning="Failed to process",
            error_message="Network timeout"
        )
        
        self.assertFalse(response.success)
        self.assertEqual(response.overall_score, 0.0)
        self.assertIn("Network timeout", response.error_message)


if __name__ == '__main__':
    # Run tests with: python manage.py test planner.tests.test_ai_service
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intelligent_task_planner.settings')
    import django
    django.setup()
    
    # Run tests
    pytest.main([__file__, '-v'])