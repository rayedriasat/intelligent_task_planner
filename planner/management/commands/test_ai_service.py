"""
Django management command to test the OpenRouter AI service.

Usage: python manage.py test_ai_service
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import asyncio

from planner.models import Task, TimeBlock
from planner.services.ai_service import OpenRouterService, get_ai_scheduling_suggestions_sync


class Command(BaseCommand):
    help = 'Test the OpenRouter AI service functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user', 
            type=str, 
            help='Username to test with (default: first user)',
            default=None
        )
        parser.add_argument(
            '--mock', 
            action='store_true',
            help='Use mock data instead of real API call'
        )

    def handle(self, *args, **options):
        self.stdout.write("🤖 Testing OpenRouter AI Service")
        self.stdout.write("=" * 50)
        
        # Get user
        username = options.get('user')
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User '{username}' not found")
                )
                return
        else:
            user = User.objects.first()
            if not user:
                self.stdout.write(
                    self.style.ERROR("No users found in database")
                )
                return
        
        self.stdout.write(f"✅ Testing with user: {user.username}")
        
        # Get or create test tasks
        tasks = self.get_or_create_test_tasks(user)
        time_blocks = self.get_or_create_test_time_blocks(user)
        
        self.stdout.write(f"📋 Found {len(tasks)} tasks and {len(time_blocks)} time blocks")
        
        # Test the service
        if options.get('mock'):
            self.test_with_mock_data(tasks, time_blocks)
        else:
            self.test_with_real_api(tasks, time_blocks)

    def get_or_create_test_tasks(self, user):
        """Get existing tasks or create test tasks."""
        unscheduled_tasks = list(user.tasks.filter(start_time__isnull=True)[:3])
        
        if not unscheduled_tasks:
            # Create some test tasks
            tomorrow = timezone.now() + timedelta(days=1)
            
            test_tasks = [
                {
                    'title': 'Complete project documentation',
                    'description': 'Write comprehensive docs for the new feature',
                    'estimated_hours': 3.0,
                    'priority': 1,
                    'deadline': tomorrow + timedelta(days=2)
                },
                {
                    'title': 'Code review session',
                    'description': 'Review team pull requests',
                    'estimated_hours': 1.5,
                    'priority': 2,
                    'deadline': tomorrow + timedelta(days=1)
                },
                {
                    'title': 'Team meeting preparation',
                    'description': 'Prepare slides and agenda',
                    'estimated_hours': 1.0,
                    'priority': 2,
                    'deadline': tomorrow + timedelta(hours=8)
                }
            ]
            
            for task_data in test_tasks:
                task = Task.objects.create(user=user, **task_data, status='todo')
                unscheduled_tasks.append(task)
                
            self.stdout.write("📝 Created 3 test tasks")
        
        return unscheduled_tasks

    def get_or_create_test_time_blocks(self, user):
        """Get existing time blocks or create test blocks."""
        tomorrow = timezone.now() + timedelta(days=1)
        
        # Look for tomorrow's availability
        existing_blocks = list(user.time_blocks.filter(
            start_time__date=tomorrow.date()
        ))
        
        if not existing_blocks:
            # Create test time blocks for tomorrow
            morning_block = TimeBlock.objects.create(
                user=user,
                start_time=tomorrow.replace(hour=9, minute=0, second=0, microsecond=0),
                end_time=tomorrow.replace(hour=12, minute=0, second=0, microsecond=0),
                is_recurring=False
            )
            
            afternoon_block = TimeBlock.objects.create(
                user=user,
                start_time=tomorrow.replace(hour=14, minute=0, second=0, microsecond=0),
                end_time=tomorrow.replace(hour=17, minute=0, second=0, microsecond=0),
                is_recurring=False
            )
            
            existing_blocks = [morning_block, afternoon_block]
            self.stdout.write("🕒 Created 2 test time blocks for tomorrow")
        
        return existing_blocks

    def test_with_real_api(self, tasks, time_blocks):
        """Test with real OpenRouter API call."""
        self.stdout.write("\n🌐 Testing with real OpenRouter API...")
        
        try:
            # Use sync wrapper
            result = get_ai_scheduling_suggestions_sync(tasks, time_blocks)
            
            if result.success:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ AI service successful!")
                )
                self.stdout.write(f"📊 Overall Score: {result.overall_score}")
                self.stdout.write(f"💭 Reasoning: {result.reasoning}")
                self.stdout.write(f"📋 Suggestions: {len(result.suggestions)}")
                
                for i, suggestion in enumerate(result.suggestions, 1):
                    self.stdout.write(f"\n  {i}. Task {suggestion.task_id}")
                    self.stdout.write(f"     Start: {suggestion.suggested_start_time}")
                    self.stdout.write(f"     End: {suggestion.suggested_end_time}")
                    self.stdout.write(f"     Confidence: {suggestion.confidence_score:.2f}")
                    self.stdout.write(f"     Reason: {suggestion.reasoning}")
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ AI service failed: {result.error_message}")
                )
                self.stdout.write(f"💭 Reasoning: {result.reasoning}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"💥 Exception during AI service test: {e}")
            )

    def test_with_mock_data(self, tasks, time_blocks):
        """Test service components with mock data."""
        self.stdout.write("\n🎭 Testing with mock data...")
        
        service = OpenRouterService()
        
        # Test data formatting
        self.stdout.write("🔧 Testing data formatting...")
        try:
            formatted_tasks = service.format_tasks_for_ai(tasks)
            formatted_blocks = service.format_time_blocks_for_ai(time_blocks)
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Formatted {len(formatted_tasks)} tasks and {len(formatted_blocks)} blocks")
            )
            
            # Test prompt creation
            prompt = service.create_ai_prompt(formatted_tasks, formatted_blocks)
            self.stdout.write(f"📝 Generated prompt ({len(prompt)} characters)")
            
            # Show sample of prompt
            if len(prompt) > 200:
                self.stdout.write(f"📄 Prompt preview: {prompt[:200]}...")
            else:
                self.stdout.write(f"📄 Full prompt: {prompt}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error in data formatting: {e}")
            )
        
        # Test response parsing
        self.stdout.write("\n🔍 Testing response parsing...")
        
        mock_api_response = {
            "choices": [
                {
                    "message": {
                        "content": """
                        {
                            "success": true,
                            "suggestions": [
                                {
                                    "task_id": %d,
                                    "suggested_start_time": "2024-01-15T09:00:00",
                                    "suggested_end_time": "2024-01-15T12:00:00",
                                    "confidence_score": 0.95,
                                    "reasoning": "High priority task fits perfectly in morning slot"
                                }
                            ],
                            "overall_score": 0.9,
                            "reasoning": "Optimal schedule with excellent time utilization"
                        }
                        """ % tasks[0].id
                    }
                }
            ]
        }
        
        try:
            parsed_response = service.parse_ai_response(mock_api_response)
            
            if parsed_response.success:
                self.stdout.write(
                    self.style.SUCCESS("✅ Response parsing successful!")
                )
                self.stdout.write(f"📊 Mock Score: {parsed_response.overall_score}")
                self.stdout.write(f"💭 Mock Reasoning: {parsed_response.reasoning}")
                self.stdout.write(f"📋 Mock Suggestions: {len(parsed_response.suggestions)}")
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Response parsing failed: {parsed_response.error_message}")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error in response parsing: {e}")
            )
        
        self.stdout.write("\n🎉 Mock testing completed!")

    def style_header(self, text):
        """Style header text."""
        return self.style.SUCCESS(f"\n{text}\n" + "=" * len(text))