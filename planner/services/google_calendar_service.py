"""
Google Calendar API service for syncing tasks with Google Calendar.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from allauth.socialaccount.models import SocialToken
from ..models import Task, GoogleCalendarIntegration, GoogleCalendarEvent, CalendarSyncLog

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service class for Google Calendar API operations."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, user: User):
        self.user = user
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Calendar API service."""
        try:
            # Get user's Google OAuth token
            social_token = SocialToken.objects.filter(
                account__user=self.user,
                account__provider='google'
            ).first()
            
            if not social_token:
                raise ValueError("No Google OAuth token found for user")
            
            # Create credentials with all required fields
            credentials = Credentials(
                token=social_token.token,
                refresh_token=social_token.token_secret,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
                client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                scopes=self.SCOPES
            )
            
            # Build service
            self.service = build('calendar', 'v3', credentials=credentials)
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service for user {self.user.id}: {e}")
            raise
    
    def get_primary_calendar(self) -> str:
        """Get the user's primary Google Calendar ID."""
        try:
            calendar_list = self.service.calendarList().list().execute()
            
            for calendar in calendar_list.get('items', []):
                if calendar.get('primary'):
                    return calendar['id']
            
            # Fallback to user's email
            return self.user.email
            
        except HttpError as e:
            logger.error(f"Error getting primary calendar: {e}")
            raise
    
    def sync_tasks_to_google(self, tasks: List[Task] = None) -> Dict:
        """Sync tasks to Google Calendar."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        sync_log = CalendarSyncLog.objects.create(
            user=self.user,
            sync_type='manual',
            status='failed'
        )
        start_time = timezone.now()
        
        try:
            if tasks is None:
                # Get all scheduled tasks that need syncing
                tasks = Task.objects.filter(
                    user=self.user,
                    start_time__isnull=False,
                    status__in=['todo', 'in_progress']
                )
            
            integration, created = GoogleCalendarIntegration.objects.get_or_create(
                user=self.user,
                defaults={'google_calendar_id': self.get_primary_calendar()}
            )
            
            events_created = 0
            events_updated = 0
            errors = []
            
            for task in tasks:
                try:
                    google_event, created = GoogleCalendarEvent.objects.get_or_create(
                        task=task,
                        defaults={
                            'google_event_id': '',
                            'google_calendar_id': integration.google_calendar_id
                        }
                    )
                    
                    event_data = self._task_to_event(task)
                    
                    if created or not google_event.google_event_id:
                        # Create new event
                        event = self.service.events().insert(
                            calendarId=integration.google_calendar_id,
                            body=event_data
                        ).execute()
                        
                        google_event.google_event_id = event['id']
                        google_event.etag = event.get('etag', '')
                        google_event.save()
                        events_created += 1
                        
                    else:
                        # Update existing event
                        event = self.service.events().update(
                            calendarId=integration.google_calendar_id,
                            eventId=google_event.google_event_id,
                            body=event_data
                        ).execute()
                        
                        google_event.etag = event.get('etag', '')
                        google_event.save()
                        events_updated += 1
                        
                except HttpError as e:
                    error_msg = f"Error syncing task {task.id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Update sync log
            sync_log.status = 'success' if not errors else 'partial'
            sync_log.events_created = events_created
            sync_log.events_updated = events_updated
            sync_log.events_synced = events_created + events_updated
            sync_log.error_message = '; '.join(errors) if errors else ''
            sync_log.sync_duration = timezone.now() - start_time
            sync_log.save()
            
            # Update integration last sync time
            integration.last_sync = timezone.now()
            integration.save()
            
            return {
                'success': True,
                'events_created': events_created,
                'events_updated': events_updated,
                'errors': errors
            }
            
        except Exception as e:
            sync_log.error_message = str(e)
            sync_log.sync_duration = timezone.now() - start_time
            sync_log.save()
            logger.error(f"Google Calendar sync failed: {e}")
            raise
    
    def sync_from_google(self, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """Sync events from Google Calendar to tasks."""
        if not self.service:
            raise ValueError("Google Calendar service not initialized")
        
        if not start_date:
            start_date = timezone.now()
        if not end_date:
            end_date = start_date + timedelta(days=30)
        
        sync_log = CalendarSyncLog.objects.create(
            user=self.user,
            sync_type='manual',
            status='failed'
        )
        start_time = timezone.now()
        
        try:
            integration = GoogleCalendarIntegration.objects.get(user=self.user)
            
            # Get events from Google Calendar
            events_result = self.service.events().list(
                calendarId=integration.google_calendar_id,
                timeMin=start_date.isoformat(),
                timeMax=end_date.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            events_created = 0
            events_updated = 0
            errors = []
            
            for event in events:
                try:
                    # Skip all-day events and events without start time
                    if 'dateTime' not in event.get('start', {}):
                        continue
                    
                    # Check if this event is already linked to a task
                    google_event = GoogleCalendarEvent.objects.filter(
                        google_event_id=event['id']
                    ).first()
                    
                    if google_event:
                        # Update existing task
                        task = google_event.task
                        if self._update_task_from_event(task, event):
                            events_updated += 1
                    else:
                        # Create new task
                        task = self._create_task_from_event(event)
                        if task:
                            GoogleCalendarEvent.objects.create(
                                task=task,
                                google_event_id=event['id'],
                                google_calendar_id=integration.google_calendar_id,
                                etag=event.get('etag', '')
                            )
                            events_created += 1
                            
                except Exception as e:
                    error_msg = f"Error processing event {event.get('id')}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Update sync log
            sync_log.status = 'success' if not errors else 'partial'
            sync_log.events_created = events_created
            sync_log.events_updated = events_updated
            sync_log.events_synced = events_created + events_updated
            sync_log.error_message = '; '.join(errors) if errors else ''
            sync_log.sync_duration = timezone.now() - start_time
            sync_log.save()
            
            # Update integration last sync time
            integration.last_sync = timezone.now()
            integration.save()
            
            return {
                'success': True,
                'events_created': events_created,
                'events_updated': events_updated,
                'errors': errors
            }
            
        except Exception as e:
            sync_log.error_message = str(e)
            sync_log.sync_duration = timezone.now() - start_time
            sync_log.save()
            logger.error(f"Google Calendar import failed: {e}")
            raise
    
    def _task_to_event(self, task: Task) -> Dict:
        """Convert a Task object to Google Calendar event data."""
        # Get task times and ensure they're in the correct timezone
        start_time = task.start_time
        end_time = task.end_time
        
        if not end_time and task.estimated_hours:
            end_time = start_time + timedelta(hours=float(task.estimated_hours))
        
        # Tasks are already stored in the correct timezone, don't convert them
        # Just use the stored times directly
        if timezone.is_aware(start_time):
            start_local = start_time
            end_local = end_time if end_time else None
        else:
            # Make timezone-aware in local timezone
            start_local = timezone.make_aware(start_time)
            end_local = timezone.make_aware(end_time) if end_time else None
        
        # Format for Google Calendar API using ISO format like Google sends to us
        # This ensures consistent timezone handling in both directions
        event_data = {
            'summary': task.title,
            'description': f"{task.description or ''}\n\nPriority: {task.get_priority_display()}\nStatus: {task.get_status_display()}",
            'start': {
                'dateTime': start_local.isoformat(),  # Use ISO format with timezone offset
            },
            'end': {
                'dateTime': end_local.isoformat(),  # Use ISO format with timezone offset
            },
            'colorId': self._get_color_for_priority(task.priority),
            'extendedProperties': {
                'private': {
                    'taskId': str(task.id),
                    'source': 'task_planner'
                }
            }
        }
        
        return event_data
    
    def _create_task_from_event(self, event: Dict) -> Optional[Task]:
        """Create a Task from Google Calendar event."""
        try:
            # Skip events that were created by this app
            if (event.get('extendedProperties', {})
                    .get('private', {})
                    .get('source') == 'task_planner'):
                return None
            
            start_time = datetime.fromisoformat(
                event['start']['dateTime'].replace('Z', '+00:00')
            )
            end_time = datetime.fromisoformat(
                event['end']['dateTime'].replace('Z', '+00:00')
            )
            
            # Calculate estimated hours
            duration = end_time - start_time
            estimated_hours = duration.total_seconds() / 3600
            
            task = Task.objects.create(
                user=self.user,
                title=event.get('summary', 'Untitled Event'),
                description=event.get('description', ''),
                deadline=end_time,  # Use end time as deadline
                priority=2,  # Default priority
                estimated_hours=max(estimated_hours, 0.5),  # Minimum 30 minutes
                start_time=start_time,
                end_time=end_time,
                status='todo'
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Error creating task from event: {e}")
            return None
    
    def _update_task_from_event(self, task: Task, event: Dict) -> bool:
        """Update a Task from Google Calendar event."""
        try:
            start_time = datetime.fromisoformat(
                event['start']['dateTime'].replace('Z', '+00:00')
            )
            end_time = datetime.fromisoformat(
                event['end']['dateTime'].replace('Z', '+00:00')
            )
            
            # Update task fields
            task.title = event.get('summary', task.title)
            task.description = event.get('description', task.description)
            task.start_time = start_time
            task.end_time = end_time
            
            # Calculate estimated hours
            duration = end_time - start_time
            task.estimated_hours = max(duration.total_seconds() / 3600, 0.5)
            
            task.save()
            return True
            
        except Exception as e:
            logger.error(f"Error updating task from event: {e}")
            return False
    
    def _get_color_for_priority(self, priority: int) -> str:
        """Get Google Calendar color ID based on task priority."""
        color_map = {
            1: '2',  # Green for low priority
            2: '1',  # Blue for medium priority  
            3: '5',  # Yellow for high priority
            4: '11', # Red for urgent priority
        }
        return color_map.get(priority, '1')
    
    def delete_event(self, task: Task) -> bool:
        """Delete a Google Calendar event for a task."""
        try:
            google_event = GoogleCalendarEvent.objects.get(task=task)
            
            self.service.events().delete(
                calendarId=google_event.google_calendar_id,
                eventId=google_event.google_event_id
            ).execute()
            
            google_event.delete()
            return True
            
        except GoogleCalendarEvent.DoesNotExist:
            # Event not synced to Google
            return True
        except HttpError as e:
            if e.resp.status == 404:
                # Event already deleted in Google Calendar
                google_event.delete()
                return True
            logger.error(f"Error deleting Google Calendar event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event: {e}")
            return False
    
    def sync_task_to_google(self, task: Task) -> bool:
        """Sync a single task to Google Calendar."""
        if not self.service or not task.start_time:
            return False
            
        try:
            integration = GoogleCalendarIntegration.objects.filter(user=self.user).first()
            if not integration or not integration.is_enabled:
                return False
                
            # Check if task already has a Google Calendar event
            existing_event = GoogleCalendarEvent.objects.filter(
                task=task,
                calendar_id=integration.calendar_id
            ).first()
            
            event_data = self._task_to_event(task)
            
            if existing_event:
                # Update existing event
                self.service.events().update(
                    calendarId=integration.calendar_id,
                    eventId=existing_event.google_event_id,
                    body=event_data
                ).execute()
                logger.info(f"Updated Google Calendar event for task {task.id}")
            else:
                # Create new event
                event = self.service.events().insert(
                    calendarId=integration.calendar_id,
                    body=event_data
                ).execute()
                
                # Save the relationship
                GoogleCalendarEvent.objects.create(
                    task=task,
                    google_event_id=event['id'],
                    calendar_id=integration.calendar_id
                )
                logger.info(f"Created Google Calendar event for task {task.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing task {task.id} to Google Calendar: {e}")
            return False
    
    def delete_google_event(self, google_event_id: str) -> bool:
        """Delete a specific Google Calendar event by ID."""
        if not self.service:
            return False
            
        try:
            integration = GoogleCalendarIntegration.objects.filter(user=self.user).first()
            if not integration:
                return False
                
            self.service.events().delete(
                calendarId=integration.calendar_id,
                eventId=google_event_id
            ).execute()
            
            # Remove the relationship record
            GoogleCalendarEvent.objects.filter(
                google_event_id=google_event_id,
                calendar_id=integration.calendar_id
            ).delete()
            
            logger.info(f"Deleted Google Calendar event {google_event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event {google_event_id}: {e}")
            return False
    
    def sync_task_to_google(self, task: Task) -> bool:
        """Sync a single task to Google Calendar."""
        if not self.service or not task.start_time:
            return False
            
        try:
            integration = GoogleCalendarIntegration.objects.filter(user=self.user).first()
            if not integration or not integration.is_enabled:
                return False
            
            # Check if task already has a Google Calendar event
            existing_event = GoogleCalendarEvent.objects.filter(
                task=task,
                calendar_id=integration.calendar_id
            ).first()
            
            # Convert task to Google Calendar event format
            event_data = self._task_to_event(task)
            
            if existing_event:
                # Update existing event
                updated_event = self.service.events().update(
                    calendarId=integration.calendar_id,
                    eventId=existing_event.google_event_id,
                    body=event_data
                ).execute()
                logger.info(f"Updated Google Calendar event for task {task.id}")
            else:
                # Create new event
                created_event = self.service.events().insert(
                    calendarId=integration.calendar_id,
                    body=event_data
                ).execute()
                
                # Store the relationship
                GoogleCalendarEvent.objects.create(
                    task=task,
                    google_event_id=created_event['id'],
                    calendar_id=integration.calendar_id
                )
                logger.info(f"Created Google Calendar event for task {task.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing task {task.id} to Google Calendar: {e}")
            return False
    
    def delete_google_event(self, google_event_id: str) -> bool:
        """Delete a Google Calendar event by its ID."""
        if not self.service:
            return False
            
        try:
            integration = GoogleCalendarIntegration.objects.filter(user=self.user).first()
            if not integration:
                return False
            
            # Delete from Google Calendar
            self.service.events().delete(
                calendarId=integration.calendar_id,
                eventId=google_event_id
            ).execute()
            
            # Remove the relationship record
            GoogleCalendarEvent.objects.filter(
                google_event_id=google_event_id,
                calendar_id=integration.calendar_id
            ).delete()
            
            logger.info(f"Deleted Google Calendar event {google_event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event {google_event_id}: {e}")
            return False
