"""
Canvas LMS API service for syncing assignments, todos, and announcements.
"""
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from ..models import (
    Task, CanvasIntegration, CanvasAssignment, CanvasTodo, 
    CanvasAnnouncement, CanvasSyncLog
)

logger = logging.getLogger(__name__)


class CanvasService:
    """Service class for Canvas LMS API operations."""
    
    def __init__(self, user: User):
        self.user = user
        self.integration = None
        self.session = requests.Session()
        self._initialize_integration()
    
    def _initialize_integration(self):
        """Initialize Canvas integration for the user."""
        try:
            self.integration = CanvasIntegration.objects.get(user=self.user)
            if not self.integration.is_configured:
                raise ValueError("Canvas integration not properly configured")
            
            # Set up session with authorization
            self.session.headers.update({
                'Authorization': f'Bearer {self.integration.canvas_access_token}',
                'Content-Type': 'application/json',
                'User-Agent': 'TaskPlanner/1.0'
            })
            
        except CanvasIntegration.DoesNotExist:
            raise ValueError("Canvas integration not found for user")
        except Exception as e:
            logger.error(f"Failed to initialize Canvas service for user {self.user.id}: {e}")
            raise
    
    def _make_api_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Canvas API."""
        if not self.integration.canvas_base_url:
            raise ValueError("Canvas base URL not configured")
        
        url = f"{self.integration.canvas_base_url.rstrip('/')}/api/v1/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Canvas API request failed for {url}: {e}")
            raise
    
    def _get_all_courses(self) -> List[Dict]:
        """Get all courses the user is enrolled in."""
        try:
            return self._make_api_request('courses', {
                'enrollment_state': 'active',
                'per_page': 100
            })
        except Exception as e:
            logger.error(f"Error fetching courses: {e}")
            return []
    
    def sync_assignments(self) -> Dict:
        """Sync assignments from Canvas to tasks."""
        sync_log = CanvasSyncLog.objects.create(
            user=self.user,
            sync_type='assignments',
            status='failed'
        )
        start_time = timezone.now()
        
        try:
            courses = self._get_all_courses()
            assignments_synced = 0
            tasks_created = 0
            tasks_updated = 0
            errors = []
            
            for course in courses:
                try:
                    course_id = str(course['id'])
                    course_name = course.get('name', 'Unknown Course')
                    
                    # Get assignments for this course
                    assignments = self._make_api_request(f'courses/{course_id}/assignments', {
                        'per_page': 100,
                        'order_by': 'due_at'
                    })
                    
                    for assignment_data in assignments:
                        try:
                            assignment, task_created, task_updated = self._process_assignment(
                                assignment_data, course_id, course_name
                            )
                            if assignment:
                                assignments_synced += 1
                                if task_created:
                                    tasks_created += 1
                                if task_updated:
                                    tasks_updated += 1
                                    
                        except Exception as e:
                            error_msg = f"Error processing assignment {assignment_data.get('id')}: {e}"
                            logger.error(error_msg)
                            errors.append(error_msg)
                            
                except Exception as e:
                    error_msg = f"Error fetching assignments for course {course.get('id')}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Update sync log
            sync_log.status = 'success' if not errors else 'partial'
            sync_log.assignments_synced = assignments_synced
            sync_log.tasks_created = tasks_created
            sync_log.tasks_updated = tasks_updated
            sync_log.error_message = '; '.join(errors) if errors else ''
            sync_log.sync_duration = timezone.now() - start_time
            sync_log.save()
            
            # Update integration last sync time
            self.integration.last_sync = timezone.now()
            self.integration.save()
            
            return {
                'success': True,
                'assignments_synced': assignments_synced,
                'tasks_created': tasks_created,
                'tasks_updated': tasks_updated,
                'errors': errors
            }
            
        except Exception as e:
            sync_log.error_message = str(e)
            sync_log.sync_duration = timezone.now() - start_time
            sync_log.save()
            logger.error(f"Canvas assignment sync failed: {e}")
            raise
    
    def sync_todos(self) -> Dict:
        """Sync planner items (todos) from Canvas."""
        sync_log = CanvasSyncLog.objects.create(
            user=self.user,
            sync_type='todos',
            status='failed'
        )
        start_time = timezone.now()
        
        try:
            # Get planner items
            planner_items = self._make_api_request('planner/items', {
                'per_page': 100,
                'start_date': timezone.now().date().isoformat(),
                'end_date': (timezone.now() + timedelta(days=365)).date().isoformat()
            })
            
            todos_synced = 0
            tasks_created = 0
            tasks_updated = 0
            errors = []
            
            for item_data in planner_items:
                try:
                    todo, task_created, task_updated = self._process_todo_item(item_data)
                    if todo:
                        todos_synced += 1
                        if task_created:
                            tasks_created += 1
                        if task_updated:
                            tasks_updated += 1
                            
                except Exception as e:
                    error_msg = f"Error processing todo item {item_data.get('plannable_id')}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Update sync log
            sync_log.status = 'success' if not errors else 'partial'
            sync_log.todos_synced = todos_synced
            sync_log.tasks_created = tasks_created
            sync_log.tasks_updated = tasks_updated
            sync_log.error_message = '; '.join(errors) if errors else ''
            sync_log.sync_duration = timezone.now() - start_time
            sync_log.save()
            
            return {
                'success': True,
                'todos_synced': todos_synced,
                'tasks_created': tasks_created,
                'tasks_updated': tasks_updated,
                'errors': errors
            }
            
        except Exception as e:
            sync_log.error_message = str(e)
            sync_log.sync_duration = timezone.now() - start_time
            sync_log.save()
            logger.error(f"Canvas todo sync failed: {e}")
            raise
    
    def sync_announcements(self) -> Dict:
        """Sync announcements from Canvas."""
        sync_log = CanvasSyncLog.objects.create(
            user=self.user,
            sync_type='announcements',
            status='failed'
        )
        start_time = timezone.now()
        
        try:
            courses = self._get_all_courses()
            announcements_synced = 0
            errors = []
            
            # Get announcements from all courses
            context_codes = [f"course_{course['id']}" for course in courses]
            
            announcements = self._make_api_request('announcements', {
                'context_codes[]': context_codes,
                'per_page': 100,
                'start_date': (timezone.now() - timedelta(days=30)).date().isoformat()
            })
            
            for announcement_data in announcements:
                try:
                    announcement = self._process_announcement(announcement_data)
                    if announcement:
                        announcements_synced += 1
                        
                except Exception as e:
                    error_msg = f"Error processing announcement {announcement_data.get('id')}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Update sync log
            sync_log.status = 'success' if not errors else 'partial'
            sync_log.announcements_synced = announcements_synced
            sync_log.error_message = '; '.join(errors) if errors else ''
            sync_log.sync_duration = timezone.now() - start_time
            sync_log.save()
            
            return {
                'success': True,
                'announcements_synced': announcements_synced,
                'errors': errors
            }
            
        except Exception as e:
            sync_log.error_message = str(e)
            sync_log.sync_duration = timezone.now() - start_time
            sync_log.save()
            logger.error(f"Canvas announcement sync failed: {e}")
            raise
    
    def full_sync(self) -> Dict:
        """Perform a full sync of all Canvas data."""
        results = {
            'assignments': {'success': False},
            'todos': {'success': False},
            'announcements': {'success': False},
            'overall_success': False
        }
        
        try:
            # Sync assignments
            if self.integration.sync_assignments:
                results['assignments'] = self.sync_assignments()
            
            # Sync todos
            if self.integration.sync_todos:
                results['todos'] = self.sync_todos()
            
            # Sync announcements
            if self.integration.sync_announcements:
                results['announcements'] = self.sync_announcements()
            
            # Determine overall success
            results['overall_success'] = all(
                result.get('success', False) for result in [
                    results['assignments'], results['todos'], results['announcements']
                ] if result.get('success') is not False
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Canvas full sync failed: {e}")
            return results
    
    def _process_assignment(self, assignment_data: Dict, course_id: str, course_name: str) -> Tuple[Optional[CanvasAssignment], bool, bool]:
        """Process a Canvas assignment and create/update corresponding models."""
        try:
            canvas_id = str(assignment_data['id'])
            
            # Get or create Canvas assignment
            canvas_assignment, created = CanvasAssignment.objects.get_or_create(
                user=self.user,
                canvas_id=canvas_id,
                defaults={
                    'course_id': course_id,
                    'course_name': course_name,
                    'title': assignment_data.get('name', 'Untitled Assignment'),
                    'description': assignment_data.get('description', ''),
                    'due_date': self._parse_canvas_date(assignment_data.get('due_at')),
                    'points_possible': assignment_data.get('points_possible'),
                    'submission_types': assignment_data.get('submission_types', []),
                    'html_url': assignment_data.get('html_url', ''),
                    'canvas_updated_at': self._parse_canvas_date(assignment_data.get('updated_at'))
                }
            )
            
            task_created = False
            task_updated = False
            
            # Create or update associated task
            if canvas_assignment.task:
                # Update existing task
                task = canvas_assignment.task
                if self._should_update_task(task, assignment_data):
                    self._update_task_from_assignment(task, assignment_data, course_name)
                    task_updated = True
            else:
                # Create new task
                task = self._create_task_from_assignment(assignment_data, course_name, canvas_id)
                if task:
                    canvas_assignment.task = task
                    canvas_assignment.save()
                    task_created = True
            
            return canvas_assignment, task_created, task_updated
            
        except Exception as e:
            logger.error(f"Error processing assignment: {e}")
            return None, False, False
    
    def _process_todo_item(self, item_data: Dict) -> Tuple[Optional[CanvasTodo], bool, bool]:
        """Process a Canvas planner item and create/update corresponding models."""
        try:
            canvas_id = str(item_data['plannable_id'])
            plannable_type = item_data.get('plannable_type', 'unknown')
            
            canvas_todo, created = CanvasTodo.objects.get_or_create(
                user=self.user,
                canvas_id=canvas_id,
                defaults={
                    'plannable_type': plannable_type,
                    'plannable_id': canvas_id,
                    'title': item_data.get('plannable', {}).get('title', 'Untitled Item'),
                    'course_id': str(item_data.get('context_id', '')),
                    'course_name': item_data.get('context_name', ''),
                    'due_date': self._parse_canvas_date(item_data.get('plannable_date')),
                    'html_url': item_data.get('html_url', ''),
                    'canvas_updated_at': self._parse_canvas_date(item_data.get('plannable', {}).get('updated_at'))
                }
            )
            
            task_created = False
            task_updated = False
            
            # Create or update associated task
            if canvas_todo.task:
                if self._should_update_task(canvas_todo.task, item_data.get('plannable', {})):
                    self._update_task_from_todo(canvas_todo.task, item_data)
                    task_updated = True
            else:
                task = self._create_task_from_todo(item_data, canvas_id)
                if task:
                    canvas_todo.task = task
                    canvas_todo.save()
                    task_created = True
            
            return canvas_todo, task_created, task_updated
            
        except Exception as e:
            logger.error(f"Error processing todo item: {e}")
            return None, False, False
    
    def _process_announcement(self, announcement_data: Dict) -> Optional[CanvasAnnouncement]:
        """Process a Canvas announcement."""
        try:
            canvas_id = str(announcement_data['id'])
            
            canvas_announcement, created = CanvasAnnouncement.objects.get_or_create(
                user=self.user,
                canvas_id=canvas_id,
                defaults={
                    'course_id': str(announcement_data.get('context_id', '')),
                    'course_name': announcement_data.get('context_name', ''),
                    'title': announcement_data.get('title', 'Untitled Announcement'),
                    'message': announcement_data.get('message', ''),
                    'posted_at': self._parse_canvas_date(announcement_data.get('posted_at')),
                    'html_url': announcement_data.get('html_url', ''),
                    'canvas_updated_at': self._parse_canvas_date(announcement_data.get('updated_at'))
                }
            )
            
            return canvas_announcement
            
        except Exception as e:
            logger.error(f"Error processing announcement: {e}")
            return None
    
    def _create_task_from_assignment(self, assignment_data: Dict, course_name: str, canvas_id: str) -> Optional[Task]:
        """Create a task from Canvas assignment data."""
        try:
            due_date = self._parse_canvas_date(assignment_data.get('due_at'))
            if not due_date:
                due_date = timezone.now() + timedelta(days=7)  # Default deadline
            
            # Estimate hours based on points possible (rough heuristic)
            points = assignment_data.get('points_possible', 0)
            estimated_hours = max(float(points or 10) / 10, 1.0)  # Minimum 1 hour
            
            task = Task.objects.create(
                user=self.user,
                title=f"[{course_name}] {assignment_data.get('name', 'Assignment')}",
                description=assignment_data.get('description', ''),
                deadline=due_date,
                priority=self._get_priority_from_due_date(due_date),
                estimated_hours=estimated_hours,
                source='canvas',
                external_id=canvas_id,
                status='todo'
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Error creating task from assignment: {e}")
            return None
    
    def _create_task_from_todo(self, item_data: Dict, canvas_id: str) -> Optional[Task]:
        """Create a task from Canvas todo item."""
        try:
            plannable = item_data.get('plannable', {})
            due_date = self._parse_canvas_date(item_data.get('plannable_date'))
            if not due_date:
                due_date = timezone.now() + timedelta(days=7)
            
            task = Task.objects.create(
                user=self.user,
                title=f"[{item_data.get('context_name', 'Canvas')}] {plannable.get('title', 'Todo Item')}",
                description=f"Canvas {item_data.get('plannable_type', 'item')}",
                deadline=due_date,
                priority=self._get_priority_from_due_date(due_date),
                estimated_hours=1.0,  # Default 1 hour for todo items
                source='canvas',
                external_id=canvas_id,
                status='todo'
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Error creating task from todo: {e}")
            return None
    
    def _update_task_from_assignment(self, task: Task, assignment_data: Dict, course_name: str):
        """Update a task from Canvas assignment data."""
        try:
            task.title = f"[{course_name}] {assignment_data.get('name', task.title)}"
            task.description = assignment_data.get('description', task.description)
            
            new_due_date = self._parse_canvas_date(assignment_data.get('due_at'))
            if new_due_date:
                task.deadline = new_due_date
                task.priority = self._get_priority_from_due_date(new_due_date)
            
            task.save()
            
        except Exception as e:
            logger.error(f"Error updating task from assignment: {e}")
    
    def _update_task_from_todo(self, task: Task, item_data: Dict):
        """Update a task from Canvas todo item."""
        try:
            plannable = item_data.get('plannable', {})
            task.title = f"[{item_data.get('context_name', 'Canvas')}] {plannable.get('title', task.title)}"
            
            new_due_date = self._parse_canvas_date(item_data.get('plannable_date'))
            if new_due_date:
                task.deadline = new_due_date
                task.priority = self._get_priority_from_due_date(new_due_date)
            
            task.save()
            
        except Exception as e:
            logger.error(f"Error updating task from todo: {e}")
    
    def _should_update_task(self, task: Task, canvas_data: Dict) -> bool:
        """Check if task should be updated based on Canvas data."""
        # For now, always update to keep tasks in sync
        # In the future, we could check timestamps or other criteria
        return True
    
    def _parse_canvas_date(self, date_string: str) -> Optional[datetime]:
        """Parse Canvas date string to datetime object."""
        if not date_string:
            return None
        
        try:
            # Canvas typically returns ISO format dates
            if date_string.endswith('Z'):
                date_string = date_string[:-1] + '+00:00'
            
            dt = datetime.fromisoformat(date_string)
            if dt.tzinfo is None:
                dt = timezone.make_aware(dt)
            
            return dt
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse Canvas date '{date_string}': {e}")
            return None
    
    def _get_priority_from_due_date(self, due_date: datetime) -> int:
        """Calculate task priority based on due date."""
        if not due_date:
            return 2  # Medium priority
        
        now = timezone.now()
        days_until_due = (due_date - now).days
        
        if days_until_due < 1:
            return 4  # Urgent
        elif days_until_due < 3:
            return 3  # High
        elif days_until_due < 7:
            return 2  # Medium
        else:
            return 1  # Low
    
    def test_connection(self) -> Dict:
        """Test Canvas API connection."""
        try:
            # Try to fetch user profile to test connection
            user_profile = self._make_api_request('users/self/profile')
            return {
                'success': True,
                'message': f"Connected as {user_profile.get('name', 'Unknown User')}",
                'user_info': user_profile
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Connection failed: {str(e)}"
            }
