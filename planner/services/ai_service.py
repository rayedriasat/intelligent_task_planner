"""
OpenRouter AI Integration Service

This service provides AI-powered scheduling suggestions by integrating with the OpenRouter API.
It takes user tasks and time blocks, formats them for the AI, and processes the response.

Author: KajBuzz Team
Version: 1.0
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import httpx
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class TaskData:
    """Task data structure for AI API calls."""
    id: int
    title: str
    description: str
    estimated_hours: float
    priority: int
    deadline: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    status: str


@dataclass
class TimeBlockData:
    """Time block data structure for AI API calls."""
    id: int
    start_time: str
    end_time: str
    is_recurring: bool
    day_of_week: Optional[int]


@dataclass
class AIScheduleSuggestion:
    """AI-generated schedule suggestion."""
    task_id: int
    suggested_start_time: str
    suggested_end_time: str
    confidence_score: float
    reasoning: str


@dataclass
class AIResponse:
    """Structured AI response."""
    success: bool
    suggestions: List[AIScheduleSuggestion]
    overall_score: float
    reasoning: str
    error_message: Optional[str] = None


@dataclass
class AIChatResponse:
    """Structured AI chat response."""
    success: bool
    response: str
    suggestions: Optional[List[str]] = None
    context_summary: Optional[str] = None
    error_message: Optional[str] = None


class OpenRouterAPIError(Exception):
    """Custom exception for OpenRouter API errors."""
    pass


class OpenRouterService:
    """Service for interacting with OpenRouter AI API."""
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.api_url = settings.OPENROUTER_API_URL
        self.timeout = 30  # seconds
        
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")
    
    def format_tasks_for_ai(self, tasks: List) -> List[Dict[str, Any]]:
        """Format Django task objects for AI API call."""
        formatted_tasks = []
        
        for task in tasks:
            task_data = TaskData(
                id=task.id,
                title=task.title,
                description=task.description or "",
                estimated_hours=float(task.estimated_hours),
                priority=task.priority,
                deadline=task.deadline.isoformat() if task.deadline else None,
                start_time=task.start_time.isoformat() if task.start_time else None,
                end_time=task.end_time.isoformat() if task.end_time else None,
                status=task.status
            )
            formatted_tasks.append(asdict(task_data))
        
        return formatted_tasks
    
    def format_time_blocks_for_ai(self, time_blocks: List) -> List[Dict[str, Any]]:
        """Format Django time block objects for AI API call."""
        formatted_blocks = []
        
        for block in time_blocks:
            block_data = TimeBlockData(
                id=block.id,
                start_time=block.start_time.isoformat(),
                end_time=block.end_time.isoformat(),
                is_recurring=block.is_recurring,
                day_of_week=block.day_of_week
            )
            formatted_blocks.append(asdict(block_data))
        
        return formatted_blocks
    
    def create_ai_prompt(self, tasks: List[Dict], time_blocks: List[Dict]) -> str:
        """Create the AI prompt for scheduling suggestions."""
        
        current_time = timezone.now().isoformat()
        
        prompt = f"""You are an expert task scheduling assistant. Analyze the following tasks and available time blocks to provide optimal scheduling suggestions.

Current DateTime: {current_time}

TASKS TO SCHEDULE:
{json.dumps(tasks, indent=2)}

AVAILABLE TIME BLOCKS:
{json.dumps(time_blocks, indent=2)}

INSTRUCTIONS:
1. Prioritize tasks based on deadline urgency and priority level (1=Low, 2=Medium, 3=High, 4=Urgent)
2. Respect task estimated hours and fit them within available time blocks
3. Avoid scheduling conflicts with existing scheduled tasks
4. Provide confidence scores (0-1) for each suggestion
5. Include reasoning for scheduling decisions

RESPONSE FORMAT (JSON):
{{
    "success": true,
    "suggestions": [
        {{
            "task_id": 123,
            "suggested_start_time": "2024-01-15T09:00:00",
            "suggested_end_time": "2024-01-15T11:00:00",
            "confidence_score": 0.95,
            "reasoning": "High priority task scheduled during peak productivity hours"
        }}
    ],
    "overall_score": 0.87,
    "reasoning": "Overall scheduling strategy and optimization approach"
}}

Provide ONLY valid JSON response, no additional text."""

        return prompt
    
    async def call_openrouter_api(self, prompt: str) -> Dict[str, Any]:
        """Make async HTTP call to OpenRouter API."""
        
        if not self.api_key:
            raise OpenRouterAPIError("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://KajBuzz.local",
            "X-Title": "KajBuzz - Intelligent Task Planner"
        }
        
        payload = {
            "model": "openai/gpt-oss-20b:free", 
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.1,  # Low temperature for consistent scheduling logic
            "top_p": 0.9
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"Making OpenRouter API request to {self.api_url}")
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                response_data = response.json()
                logger.info(f"OpenRouter API response received: {len(str(response_data))} characters")
                return response_data
                
            except httpx.TimeoutException:
                logger.error("OpenRouter API request timed out")
                raise OpenRouterAPIError("API request timed out")
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                logger.error(f"OpenRouter API HTTP error: {error_msg}")
                raise OpenRouterAPIError(error_msg)
            except json.JSONDecodeError as e:
                logger.error(f"OpenRouter API returned invalid JSON: {e}")
                raise OpenRouterAPIError(f"Invalid JSON response: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error in OpenRouter API call: {e}")
                raise OpenRouterAPIError(f"Unexpected error: {str(e)}")
    
    def parse_ai_response(self, api_response: Dict[str, Any]) -> AIResponse:
        """Parse OpenRouter API response into structured format."""
        
        try:
            # Extract content from OpenRouter response format
            if "choices" not in api_response or not api_response["choices"]:
                raise ValueError("Invalid API response format: no choices")
            
            content = api_response["choices"][0]["message"]["content"]
            
            # Check if content is empty or None
            if not content or content.strip() == "":
                raise ValueError("Empty content in API response")
            
            logger.debug(f"Parsing AI response content: {content[:200]}...")
            
            # Clean the content - remove markdown code blocks if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            elif content.startswith('```'):
                content = content[3:]   # Remove ```
            
            if content.endswith('```'):
                content = content[:-3]  # Remove trailing ```
            
            content = content.strip()
            
            # Parse JSON content
            ai_data = json.loads(content)
            
            if not ai_data.get("success", False):
                return AIResponse(
                    success=False,
                    suggestions=[],
                    overall_score=0.0,
                    reasoning="AI indicated failure",
                    error_message=ai_data.get("error", "Unknown AI error")
                )
            
            # Parse suggestions
            suggestions = []
            for suggestion_data in ai_data.get("suggestions", []):
                suggestion = AIScheduleSuggestion(
                    task_id=suggestion_data["task_id"],
                    suggested_start_time=suggestion_data["suggested_start_time"],
                    suggested_end_time=suggestion_data["suggested_end_time"],
                    confidence_score=float(suggestion_data.get("confidence_score", 0.5)),
                    reasoning=suggestion_data.get("reasoning", "No reasoning provided")
                )
                suggestions.append(suggestion)
            
            return AIResponse(
                success=True,
                suggestions=suggestions,
                overall_score=float(ai_data.get("overall_score", 0.5)),
                reasoning=ai_data.get("reasoning", "No overall reasoning provided")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            try:
                logger.error(f"Content that failed to parse: {content[:500]}")
            except:
                logger.error("Unable to log content that failed to parse")
            return AIResponse(
                success=False,
                suggestions=[],
                overall_score=0.0,
                reasoning="Failed to parse AI response",
                error_message=f"JSON parse error: {str(e)}"
            )
        except KeyError as e:
            logger.error(f"Missing required field in AI response: {e}")
            return AIResponse(
                success=False,
                suggestions=[],
                overall_score=0.0,
                reasoning="Invalid AI response format",
                error_message=f"Missing required field: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return AIResponse(
                success=False,
                suggestions=[],
                overall_score=0.0,
                reasoning="Error processing AI response",
                error_message=str(e)
            )
    
    async def get_scheduling_suggestions(self, tasks: List, time_blocks: List) -> AIResponse:
        """
        Main method to get AI scheduling suggestions.
        
        Args:
            tasks: List of Django Task objects
            time_blocks: List of Django TimeBlock objects
            
        Returns:
            AIResponse with suggestions or error information
        """
        
        try:
            # Validate inputs
            if not tasks:
                return AIResponse(
                    success=False,
                    suggestions=[],
                    overall_score=0.0,
                    reasoning="No tasks provided",
                    error_message="No tasks to schedule"
                )
            
            if not time_blocks:
                return AIResponse(
                    success=False,
                    suggestions=[],
                    overall_score=0.0,
                    reasoning="No time blocks available",
                    error_message="No available time blocks for scheduling"
                )
            
            # Check if API key is configured
            if not self.api_key:
                logger.warning("OpenRouter API key not configured, providing fallback response")
                return self._create_fallback_response(tasks, time_blocks)
            
            # Format data for AI
            formatted_tasks = self.format_tasks_for_ai(tasks)
            formatted_blocks = self.format_time_blocks_for_ai(time_blocks)
            
            # Create AI prompt
            prompt = self.create_ai_prompt(formatted_tasks, formatted_blocks)
            
            logger.info(f"Requesting AI suggestions for {len(tasks)} tasks and {len(time_blocks)} time blocks")
            
            # Call AI API
            api_response = await self.call_openrouter_api(prompt)
            
            # Parse and return response
            ai_response = self.parse_ai_response(api_response)
            
            logger.info(f"AI suggestions received: {len(ai_response.suggestions)} suggestions, score: {ai_response.overall_score}")
            
            return ai_response
            
        except OpenRouterAPIError as e:
            logger.error(f"OpenRouter API error: {e}")
            # Provide fallback response on API error
            logger.info("Providing fallback response due to API error")
            return self._create_fallback_response(tasks, time_blocks)
        except Exception as e:
            logger.error(f"Unexpected error in get_scheduling_suggestions: {e}")
            return AIResponse(
                success=False,
                suggestions=[],
                overall_score=0.0,
                reasoning="Service error",
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def create_chat_prompt(self, user_message: str, user_context: Dict[str, Any]) -> str:
        """Create the AI prompt for chat responses with full user context."""
        
        current_time = timezone.now().isoformat()
        
        # Format the context nicely for the AI
        context_summary = f"""
USER PROFILE:
- Username: {user_context.get('user_info', {}).get('username', 'Unknown')}
- Current Time: {current_time}

SCHEDULE OVERVIEW:
- Total Tasks: {user_context.get('schedule_overview', {}).get('total_tasks', 0)}
- Scheduled Tasks: {user_context.get('schedule_overview', {}).get('scheduled_tasks', 0)}
- Unscheduled Tasks: {user_context.get('schedule_overview', {}).get('unscheduled_tasks', 0)}
- Tasks Due Today: {user_context.get('schedule_overview', {}).get('tasks_due_today', 0)}
- Tasks Due This Week: {user_context.get('schedule_overview', {}).get('tasks_due_this_week', 0)}
- Overdue Tasks: {user_context.get('schedule_overview', {}).get('overdue_tasks', 0)}

CURRENT TASKS:
{json.dumps(user_context.get('current_tasks', [])[:10], indent=2)}

AVAILABILITY:
{json.dumps(user_context.get('availability', [])[:5], indent=2)}

RECENT ACTIVITY:
{json.dumps(user_context.get('recent_activity', {}), indent=2)}
"""

        prompt = f"""You are an expert AI scheduling and productivity assistant for a task management application. 

You have full context about the user's schedule, tasks, deadlines, and productivity patterns. Analyze this information to provide helpful, personalized advice.

{context_summary}

USER MESSAGE: "{user_message}"

INSTRUCTIONS:
1. Provide a helpful, personalized response based on the user's actual data
2. Be conversational and supportive, not robotic
3. Reference specific tasks, deadlines, or patterns when relevant
4. Offer actionable advice and suggestions
5. If asked about scheduling, suggest specific time slots from their availability
6. Keep responses concise but informative
7. Generate 2-3 helpful follow-up suggestions when appropriate

RESPONSE FORMAT (JSON):
{{
    "success": true,
    "response": "Your main response to the user's message",
    "suggestions": ["Optional follow-up suggestion 1", "Optional follow-up suggestion 2"],
    "context_summary": "Brief summary of what context was most relevant to this response"
}}

Provide ONLY valid JSON response, no additional text."""

        return prompt
    
    async def get_chat_response(self, user_message: str, user_context: Dict[str, Any]) -> AIChatResponse:
        """
        Get AI chat response with full user context.
        
        Args:
            user_message: The user's chat message
            user_context: Complete user schedule and task context
            
        Returns:
            AIChatResponse with the AI's response
        """
        
        try:
            # Validate inputs
            if not user_message or not user_message.strip():
                return AIChatResponse(
                    success=False,
                    response="",
                    error_message="No message provided"
                )
            
            # Check if API key is configured
            if not self.api_key:
                logger.warning("OpenRouter API key not configured, providing fallback chat response")
                return self._create_fallback_chat_response(user_message, user_context)
            
            # Create chat prompt
            prompt = self.create_chat_prompt(user_message, user_context)
            
            logger.info(f"Requesting AI chat response for message: {user_message[:50]}...")
            
            # Call AI API
            api_response = await self.call_openrouter_api(prompt)
            
            # Parse and return response
            chat_response = self.parse_chat_response(api_response)
            
            logger.info(f"AI chat response received successfully")
            
            return chat_response
            
        except OpenRouterAPIError as e:
            logger.error(f"OpenRouter API error in chat: {e}")
            # Provide fallback response on API error
            logger.info("Providing fallback chat response due to API error")
            return self._create_fallback_chat_response(user_message, user_context)
        except Exception as e:
            logger.error(f"Unexpected error in get_chat_response: {e}")
            return AIChatResponse(
                success=False,
                response="",
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def parse_chat_response(self, api_response: Dict[str, Any]) -> AIChatResponse:
        """Parse OpenRouter API response into chat format."""
        
        try:
            # Extract content from OpenRouter response format
            if "choices" not in api_response or not api_response["choices"]:
                raise ValueError("Invalid API response format: no choices")
            
            content = api_response["choices"][0]["message"]["content"]
            
            # Check if content is empty or None
            if not content or content.strip() == "":
                raise ValueError("Empty content in API response")
            
            logger.debug(f"Parsing AI chat response content: {content[:200]}...")
            
            # Clean the content - remove markdown code blocks if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            elif content.startswith('```'):
                content = content[3:]   # Remove ```
            
            if content.endswith('```'):
                content = content[:-3]  # Remove trailing ```
            
            content = content.strip()
            
            # Parse JSON content
            chat_data = json.loads(content)
            
            if not chat_data.get("success", False):
                return AIChatResponse(
                    success=False,
                    response="I apologize, but I'm having trouble processing your request right now.",
                    error_message=chat_data.get("error", "AI indicated failure")
                )
            
            return AIChatResponse(
                success=True,
                response=chat_data.get("response", "I'm here to help with your scheduling!"),
                suggestions=chat_data.get("suggestions", []),
                context_summary=chat_data.get("context_summary", "")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI chat response as JSON: {e}")
            try:
                logger.error(f"Content that failed to parse: {content[:500]}")
            except:
                logger.error("Unable to log content that failed to parse")
            return AIChatResponse(
                success=False,
                response="I apologize, but I'm having trouble understanding the response format.",
                error_message=f"JSON parse error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error parsing AI chat response: {e}")
            return AIChatResponse(
                success=False,
                response="I apologize, but I encountered an error processing the response.",
                error_message=str(e)
            )
    
    def _create_fallback_chat_response(self, user_message: str, user_context: Dict[str, Any]) -> AIChatResponse:
        """
        Create a fallback chat response when AI API is unavailable.
        Uses basic rules to provide helpful responses.
        """
        logger.info("Creating fallback AI chat response")
        
        message_lower = user_message.lower()
        schedule_overview = user_context.get('schedule_overview', {})
        
        # Analyze the message and provide contextual responses
        if any(word in message_lower for word in ['today', 'what should i do', 'work on']):
            tasks_due_today = schedule_overview.get('tasks_due_today', 0)
            unscheduled_tasks = schedule_overview.get('unscheduled_tasks', 0)
            
            if tasks_due_today > 0:
                response = f"You have {tasks_due_today} task{'s' if tasks_due_today != 1 else ''} due today. I'd recommend starting with your highest priority items."
            elif unscheduled_tasks > 0:
                response = f"You have {unscheduled_tasks} unscheduled task{'s' if unscheduled_tasks != 1 else ''}. Consider scheduling them into your available time blocks."
            else:
                response = "Great! It looks like you're caught up with your immediate tasks. This might be a good time to plan ahead or work on longer-term projects."
                
        elif any(word in message_lower for word in ['schedule', 'week', 'upcoming']):
            total_tasks = schedule_overview.get('total_tasks', 0)
            scheduled = schedule_overview.get('scheduled_tasks', 0)
            due_this_week = schedule_overview.get('tasks_due_this_week', 0)
            
            response = f"You have {total_tasks} total tasks, with {scheduled} already scheduled. {due_this_week} tasks are due this week."
            
        elif any(word in message_lower for word in ['urgent', 'deadline', 'overdue']):
            overdue = schedule_overview.get('overdue_tasks', 0)
            due_today = schedule_overview.get('tasks_due_today', 0)
            
            if overdue > 0:
                response = f"You have {overdue} overdue task{'s' if overdue != 1 else ''}. I recommend prioritizing these immediately."
            elif due_today > 0:
                response = f"You have {due_today} task{'s' if due_today != 1 else ''} due today. These should be your top priority."
            else:
                response = "Good news! You don't have any overdue tasks or urgent deadlines today."
                
        elif any(word in message_lower for word in ['productivity', 'efficient', 'optimize']):
            response = "Here are some productivity tips: Focus on high-priority tasks during your peak energy hours, break large tasks into smaller chunks, and use time-blocking to stay organized."
            
        else:
            # Generic helpful response
            total_tasks = schedule_overview.get('total_tasks', 0)
            response = f"I'm here to help you manage your {total_tasks} tasks and optimize your schedule! Ask me about your deadlines, what to work on next, or how to improve your productivity."
        
        return AIChatResponse(
            success=True,
            response=response,
            suggestions=[
                "What should I work on today?",
                "How is my schedule this week?",
                "What tasks are urgent?"
            ],
            context_summary="Used basic scheduling logic (AI API unavailable)"
        )

    def _create_fallback_response(self, tasks: List, time_blocks: List) -> AIResponse:
        """
        Create a fallback response when AI API is unavailable.
        Uses basic scheduling logic based on priority and deadlines.
        """
        logger.info("Creating fallback AI response using basic scheduling logic")
        
        suggestions = []
        
        # Sort tasks by priority and deadline
        sorted_tasks = sorted(tasks, key=lambda t: (
            -t.priority,  # Higher priority number = higher priority (4=Urgent first, 1=Low last)
            t.deadline if t.deadline else timezone.now() + timedelta(days=365),  # Tasks without deadline go last
            t.estimated_hours  # Shorter tasks first for same priority/deadline
        ))
        
        # Sort time blocks by start time
        sorted_blocks = sorted(time_blocks, key=lambda b: b.start_time)
        
        current_block_index = 0
        
        for task in sorted_tasks:
            if current_block_index >= len(sorted_blocks):
                break  # No more available time blocks
            
            # Find a suitable time block for this task
            task_duration = timedelta(hours=float(task.estimated_hours))
            
            for i in range(current_block_index, len(sorted_blocks)):
                block = sorted_blocks[i]
                block_duration = block.end_time - block.start_time
                
                # Check if task fits in this block
                if task_duration <= block_duration:
                    # Create suggestion
                    suggested_start = block.start_time
                    suggested_end = suggested_start + task_duration
                    
                    # Calculate confidence based on how well it fits
                    time_fit_ratio = task_duration.total_seconds() / block_duration.total_seconds()
                    priority_score = task.priority / 4.0  # Convert 1-4 priority to 0.25-1.0 score (higher number = higher score)
                    confidence = min(0.9, (priority_score * 0.6) + (time_fit_ratio * 0.4))
                    
                    suggestions.append(AIScheduleSuggestion(
                        task_id=task.id,
                        suggested_start_time=suggested_start.isoformat(),
                        suggested_end_time=suggested_end.isoformat(),
                        confidence_score=confidence,
                        reasoning=f"Scheduled based on priority {task.priority} and available time slot"
                    ))
                    
                    current_block_index = i + 1
                    break
        
        # Calculate overall score
        overall_score = 0.7 if suggestions else 0.0
        if suggestions:
            avg_confidence = sum(s.confidence_score for s in suggestions) / len(suggestions)
            overall_score = min(0.8, avg_confidence)  # Cap at 0.8 for fallback
        
        return AIResponse(
            success=True,
            suggestions=suggestions,
            overall_score=overall_score,
            reasoning=f"Fallback scheduling used (API unavailable). Scheduled {len(suggestions)} out of {len(tasks)} tasks based on priority and time availability.",
            error_message=None
        )


# Convenience functions for synchronous usage
def get_ai_scheduling_suggestions_sync(tasks: List, time_blocks: List) -> AIResponse:
    """
    Synchronous wrapper for AI scheduling suggestions.
    
    Args:
        tasks: List of Django Task objects
        time_blocks: List of Django TimeBlock objects
        
    Returns:
        AIResponse with suggestions or error information
    """
    import asyncio
    
    service = OpenRouterService()
    
    try:
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            service.get_scheduling_suggestions(tasks, time_blocks)
        )
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error in sync wrapper: {e}")
        return AIResponse(
            success=False,
            suggestions=[],
            overall_score=0.0,
            reasoning="Service error",
            error_message=str(e)
        )


def get_ai_chat_response_sync(user_message: str, user_context: Dict[str, Any]) -> AIChatResponse:
    """
    Synchronous wrapper for AI chat responses.
    
    Args:
        user_message: The user's chat message
        user_context: Complete user schedule and task context
        
    Returns:
        AIChatResponse with the AI's response
    """
    import asyncio
    
    service = OpenRouterService()
    
    try:
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            service.get_chat_response(user_message, user_context)
        )
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error in chat sync wrapper: {e}")
        return AIChatResponse(
            success=False,
            response="I apologize, but I'm experiencing technical difficulties. Please try again later.",
            error_message=str(e)
        )