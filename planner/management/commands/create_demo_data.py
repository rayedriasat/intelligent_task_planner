from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from planner.models import (
    Task, TimeBlock, PomodoroSession, OptimizationHistory, 
    NotificationPreference, TaskNotification
)
from datetime import datetime, timedelta
from django.utils import timezone
import random


class Command(BaseCommand):
    help = 'Create comprehensive demo data for showcasing the intelligent task planner'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to create demo data for (defaults to "the")',
            default='the'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating demo data',
        )

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options['user'])
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User '{options['user']}' not found"))
            return

        self.stdout.write(f"Creating comprehensive demo data for user: {user.username} ({user.email})")
        
        if options['clear']:
            self.clear_existing_data(user)
        
        # Create demo data
        self.create_time_blocks(user)
        self.create_diverse_tasks(user)
        self.create_pomodoro_sessions(user)
        self.create_optimization_history(user)
        self.setup_notifications(user)
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Demo data creation completed!'))
        self.print_summary(user)

    def clear_existing_data(self, user):
        """Clear existing data for clean demo setup"""
        self.stdout.write("🧹 Clearing existing data...")
        
        # Clear tasks and related data
        user.tasks.all().delete()
        user.time_blocks.all().delete()
        user.optimization_history.all().delete()
        
        self.stdout.write("✓ Existing data cleared")

    def create_time_blocks(self, user):
        """Create realistic availability time blocks"""
        self.stdout.write("\n⏰ Creating time blocks (availability schedule)...")
        
        now = timezone.now()
        
        # Create recurring weekly availability (work schedule)
        work_days = [
            (0, "Monday", 9, 17),    # Monday 9 AM - 5 PM
            (1, "Tuesday", 9, 17),   # Tuesday 9 AM - 5 PM
            (2, "Wednesday", 9, 17), # Wednesday 9 AM - 5 PM
            (3, "Thursday", 9, 17),  # Thursday 9 AM - 5 PM
            (4, "Friday", 9, 17),    # Friday 9 AM - 5 PM
        ]
        
        for day_num, day_name, start_hour, end_hour in work_days:
            # Morning block (9 AM - 12 PM)
            morning_start = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            morning_end = morning_start + timedelta(hours=3)
            
            TimeBlock.objects.create(
                user=user,
                start_time=morning_start,
                end_time=morning_end,
                is_recurring=True,
                day_of_week=day_num
            )
            
            # Afternoon block (1 PM - 5 PM) - lunch break from 12-1
            afternoon_start = now.replace(hour=13, minute=0, second=0, microsecond=0)
            afternoon_end = afternoon_start + timedelta(hours=4)
            
            TimeBlock.objects.create(
                user=user,
                start_time=afternoon_start,
                end_time=afternoon_end,
                is_recurring=True,
                day_of_week=day_num
            )
            
            self.stdout.write(f"✓ {day_name}: {start_hour}:00-12:00, 13:00-{end_hour}:00")
        
        # Add some weekend availability (more flexible)
        # Saturday morning (10 AM - 2 PM)
        saturday_start = now.replace(hour=10, minute=0, second=0, microsecond=0)
        saturday_end = saturday_start + timedelta(hours=4)
        
        TimeBlock.objects.create(
            user=user,
            start_time=saturday_start,
            end_time=saturday_end,
            is_recurring=True,
            day_of_week=5  # Saturday
        )
        
        # Sunday evening (6 PM - 9 PM) for planning
        sunday_start = now.replace(hour=18, minute=0, second=0, microsecond=0)
        sunday_end = sunday_start + timedelta(hours=3)
        
        TimeBlock.objects.create(
            user=user,
            start_time=sunday_start,
            end_time=sunday_end,
            is_recurring=True,
            day_of_week=6  # Sunday
        )
        
        self.stdout.write("✓ Weekend availability: Saturday 10:00-14:00, Sunday 18:00-21:00")

    def create_diverse_tasks(self, user):
        """Create a diverse set of tasks showcasing different features"""
        self.stdout.write("\n📋 Creating diverse tasks for demo...")
        
        now = timezone.now()
        
        # Different types of tasks to showcase various features
        demo_tasks = [
            # Urgent/High Priority Tasks
            {
                'title': '🚨 Critical Security Patch',
                'description': 'Apply urgent security patches to production servers. This task needs immediate attention due to security vulnerabilities discovered in the latest security audit.',
                'estimated_hours': 2.5,
                'min_block_size': 1.0,
                'priority': 4,  # Urgent
                'deadline': now + timedelta(hours=8),
                'status': 'todo'
            },
            {
                'title': '📊 Board Presentation Prep',
                'description': 'Prepare quarterly presentation for board meeting. Include financial metrics, project updates, and strategic roadmap for next quarter.',
                'estimated_hours': 4.0,
                'min_block_size': 2.0,
                'priority': 4,  # Urgent
                'deadline': now + timedelta(days=2),
                'status': 'todo'
            },
            
            # High Priority Tasks
            {
                'title': '🔍 Code Review - Authentication Module',
                'description': 'Review the new OAuth2 authentication implementation. Focus on security best practices, error handling, and integration with existing user management system.',
                'estimated_hours': 3.0,
                'min_block_size': 1.5,
                'priority': 3,  # High
                'deadline': now + timedelta(days=3),
                'status': 'todo'
            },
            {
                'title': '📝 Technical Documentation Update',
                'description': 'Update API documentation with new endpoints and authentication changes. Include code examples and migration guide for existing integrations.',
                'estimated_hours': 5.0,
                'min_block_size': 1.0,
                'priority': 3,  # High
                'deadline': now + timedelta(days=4),
                'status': 'todo'
            },
            
            # Medium Priority Tasks
            {
                'title': '🎨 UI/UX Design Review',
                'description': 'Review new dashboard designs with design team. Provide feedback on user experience, accessibility, and mobile responsiveness.',
                'estimated_hours': 2.0,
                'min_block_size': 1.0,
                'priority': 2,  # Medium
                'deadline': now + timedelta(days=5),
                'status': 'todo'
            },
            {
                'title': '🧪 Automated Testing Implementation',
                'description': 'Implement automated test suite for the scheduling engine. Cover edge cases, performance testing, and integration tests.',
                'estimated_hours': 6.0,
                'min_block_size': 2.0,
                'priority': 2,  # Medium
                'deadline': now + timedelta(days=7),
                'status': 'todo'
            },
            {
                'title': '🔧 Database Performance Optimization',
                'description': 'Analyze and optimize slow database queries. Focus on the task scheduling queries and user availability calculations.',
                'estimated_hours': 4.5,
                'min_block_size': 1.5,
                'priority': 2,  # Medium
                'deadline': now + timedelta(days=8),
                'status': 'todo'
            },
            
            # Lower Priority Tasks
            {
                'title': '📚 Research: AI/ML Integration Options',
                'description': 'Research machine learning frameworks for improving task estimation accuracy. Compare TensorFlow, PyTorch, and cloud-based ML services.',
                'estimated_hours': 8.0,
                'min_block_size': 2.0,
                'priority': 1,  # Low
                'deadline': now + timedelta(days=14),
                'status': 'todo'
            },
            {
                'title': '🌐 Internationalization Setup',
                'description': 'Set up i18n framework for multi-language support. Prepare for expansion into European markets.',
                'estimated_hours': 12.0,
                'min_block_size': 3.0,
                'priority': 1,  # Low
                'deadline': now + timedelta(days=21),
                'status': 'todo'
            },
            
            # Some completed tasks to show history
            {
                'title': '✅ User Authentication Bug Fix',
                'description': 'Fixed login timeout issues affecting mobile users. Implemented proper session management and token refresh.',
                'estimated_hours': 3.0,
                'min_block_size': 1.0,
                'priority': 3,  # High
                'deadline': now - timedelta(days=2),
                'status': 'completed',
                'start_time': now - timedelta(days=3, hours=2),
                'end_time': now - timedelta(days=3, hours=-1),  # 3 hours duration
            },
            {
                'title': '✅ Weekly Team Standup',
                'description': 'Conducted weekly team standup meeting. Discussed blockers, progress updates, and sprint planning.',
                'estimated_hours': 1.0,
                'min_block_size': 1.0,
                'priority': 2,  # Medium
                'deadline': now - timedelta(days=1),
                'status': 'completed',
                'start_time': now - timedelta(days=1, hours=2),
                'end_time': now - timedelta(days=1, hours=1),
            },
            
            # In-progress tasks
            {
                'title': '🔄 API Rate Limiting Implementation',
                'description': 'Currently implementing rate limiting for API endpoints. About 60% complete - working on Redis integration for distributed rate limiting.',
                'estimated_hours': 4.0,
                'min_block_size': 1.0,
                'priority': 3,  # High
                'deadline': now + timedelta(days=6),
                'status': 'in_progress',
                'start_time': now - timedelta(hours=4),
                'end_time': now - timedelta(hours=2),
            },
            
            # Creative/Research Tasks
            {
                'title': '💡 Brainstorm: Productivity Features',
                'description': 'Brainstorming session for new productivity features. Ideas include time tracking analytics, habit formation, and goal setting.',
                'estimated_hours': 2.0,
                'min_block_size': 2.0,  # Needs uninterrupted time
                'priority': 1,  # Low
                'deadline': now + timedelta(days=10),
                'status': 'todo'
            },
            
            # Meeting/Communication Tasks
            {
                'title': '👥 Client Demo Preparation',
                'description': 'Prepare demo environment and presentation materials for client showcase. Set up sample data and test all features.',
                'estimated_hours': 3.5,
                'min_block_size': 1.5,
                'priority': 3,  # High
                'deadline': now + timedelta(days=5),
                'status': 'todo'
            },
        ]
        
        created_tasks = []
        for task_data in demo_tasks:
            task = Task.objects.create(user=user, **task_data)
            created_tasks.append(task)
            
            status_icon = {'todo': '📝', 'in_progress': '🔄', 'completed': '✅'}[task.status]
            priority_text = {1: 'Low', 2: 'Medium', 3: 'High', 4: 'Urgent'}[task.priority]
            
            self.stdout.write(f"✓ {status_icon} {task.title[:50]}... (P{task.priority}-{priority_text}, {task.estimated_hours}h)")
        
        self.stdout.write(f"Created {len(created_tasks)} diverse tasks")

    def create_pomodoro_sessions(self, user):
        """Create some Pomodoro session history"""
        self.stdout.write("\n🍅 Creating Pomodoro session history...")
        
        # Get some completed and in-progress tasks
        completed_tasks = user.tasks.filter(status='completed')
        in_progress_tasks = user.tasks.filter(status='in_progress')
        
        sessions_created = 0
        
        # Create sessions for completed tasks
        for task in completed_tasks:
            if task.start_time and task.end_time:
                # Create 2-3 pomodoro sessions per completed task
                num_sessions = random.randint(2, 4)
                session_start = task.start_time
                
                for i in range(num_sessions):
                    # Focus session (25 minutes)
                    PomodoroSession.objects.create(
                        task=task,
                        session_type='focus',
                        status='completed',
                        planned_duration=25,
                        actual_duration=random.randint(23, 27),  # Slight variation
                        start_time=session_start,
                        end_time=session_start + timedelta(minutes=25),
                        notes=f"Productive session {i+1} - good focus maintained"
                    )
                    
                    sessions_created += 1
                    session_start += timedelta(minutes=30)  # Include break time
        
        # Create sessions for in-progress tasks
        for task in in_progress_tasks:
            if task.start_time:
                # Create 1-2 completed sessions and 1 active session
                num_completed = random.randint(1, 2)
                session_start = task.start_time
                
                for i in range(num_completed):
                    PomodoroSession.objects.create(
                        task=task,
                        session_type='focus',
                        status='completed',
                        planned_duration=25,
                        actual_duration=random.randint(22, 28),
                        start_time=session_start,
                        end_time=session_start + timedelta(minutes=25),
                        notes=f"Session {i+1} completed - making good progress"
                    )
                    sessions_created += 1
                    session_start += timedelta(minutes=30)
        
        self.stdout.write(f"✓ Created {sessions_created} Pomodoro sessions")

    def create_optimization_history(self, user):
        """Create some optimization history to show AI scheduling in action"""
        self.stdout.write("\n🤖 Creating optimization history...")
        
        now = timezone.now()
        
        # Create a few optimization runs from the past week
        optimization_runs = [
            {
                'timestamp': now - timedelta(days=3),
                'scheduled_count': 8,
                'unscheduled_count': 2,
                'utilization_rate': 0.85,
                'total_hours_scheduled': 24.5,
                'was_overloaded': False,
                'optimization_decisions': {
                    'priority_sorting': 'deadline_and_priority_based',
                    'scheduling_strategy': 'greedy_fit',
                    'conflicts_resolved': 2,
                    'tasks_rescheduled': 1
                },
                'recommendations': [
                    'Consider extending Friday availability by 2 hours',
                    'High-priority tasks scheduled for optimal focus time',
                    'Buffer time maintained between complex tasks'
                ]
            },
            {
                'timestamp': now - timedelta(days=1),
                'scheduled_count': 6,
                'unscheduled_count': 4,
                'utilization_rate': 0.95,
                'total_hours_scheduled': 28.0,
                'was_overloaded': True,
                'overload_ratio': 1.15,
                'excess_hours': 4.5,
                'optimization_decisions': {
                    'priority_sorting': 'urgency_first',
                    'scheduling_strategy': 'priority_based',
                    'overload_handling': 'defer_low_priority',
                    'tasks_deferred': 4
                },
                'recommendations': [
                    'Schedule overflow: 4.5 hours of tasks could not be scheduled',
                    'Consider deferring low-priority tasks to next week',
                    'Weekend time block might be needed for urgent tasks',
                    'Delegate research tasks to reduce workload'
                ]
            }
        ]
        
        for opt_data in optimization_runs:
            # Create dummy previous task state
            previous_state = [
                {'id': task.id, 'start_time': None, 'end_time': None, 'is_locked': False, 'status': task.status}
                for task in user.tasks.all()[:5]  # Sample of tasks
            ]
            
            OptimizationHistory.objects.create(
                user=user,
                timestamp=opt_data['timestamp'],
                scheduled_count=opt_data['scheduled_count'],
                unscheduled_count=opt_data['unscheduled_count'],
                utilization_rate=opt_data['utilization_rate'],
                total_hours_scheduled=opt_data['total_hours_scheduled'],
                was_overloaded=opt_data.get('was_overloaded', False),
                overload_ratio=opt_data.get('overload_ratio'),
                excess_hours=opt_data.get('excess_hours'),
                previous_task_state=previous_state,
                optimization_decisions=opt_data['optimization_decisions'],
                recommendations=opt_data['recommendations']
            )
        
        self.stdout.write(f"✓ Created {len(optimization_runs)} optimization history entries")

    def setup_notifications(self, user):
        """Setup notification preferences and create some sample notifications"""
        self.stdout.write("\n🔔 Setting up notifications...")
        
        # Ensure notification preferences exist (should be auto-created)
        prefs, created = NotificationPreference.objects.get_or_create(user=user)
        if created:
            self.stdout.write("✓ Created notification preferences")
        
        # Enable all notification types for demo
        prefs.task_reminder_enabled = True
        prefs.task_reminder_minutes = 30  # 30 minutes before
        prefs.task_reminder_method = 'both'
        
        prefs.deadline_warning_enabled = True
        prefs.deadline_warning_hours = 12  # 12 hours before
        prefs.deadline_warning_method = 'both'
        
        prefs.schedule_optimization_enabled = True
        prefs.schedule_optimization_method = 'browser'
        
        prefs.pomodoro_break_enabled = True
        prefs.save()
        
        # Create some sample notifications for upcoming tasks
        upcoming_tasks = user.tasks.filter(
            status='todo',
            start_time__isnull=False,
            start_time__gt=timezone.now()
        )[:3]  # Get first 3 upcoming scheduled tasks
        
        notifications_created = 0
        for task in upcoming_tasks:
            # Task reminder notification
            reminder_time = task.start_time - timedelta(minutes=30)
            if reminder_time > timezone.now():
                TaskNotification.objects.create(
                    task=task,
                    notification_type='task_reminder',
                    scheduled_time=reminder_time,
                    status='pending',
                    delivery_method='both',
                    title=f'Upcoming Task: {task.title}',
                    message=f'Your task "{task.title}" is starting in 30 minutes. Duration: {task.estimated_hours} hours.'
                )
                notifications_created += 1
            
            # Deadline warning for tasks due soon
            if task.deadline:
                warning_time = task.deadline - timedelta(hours=12)
                if warning_time > timezone.now():
                    TaskNotification.objects.create(
                        task=task,
                        notification_type='deadline_warning',
                        scheduled_time=warning_time,
                        status='pending',
                        delivery_method='both',
                        title=f'Deadline Approaching: {task.title}',
                        message=f'Your task "{task.title}" is due in 12 hours. Make sure to complete it on time!'
                    )
                    notifications_created += 1
        
        self.stdout.write(f"✓ Set up notification preferences and created {notifications_created} pending notifications")

    def print_summary(self, user):
        """Print a summary of created demo data"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📊 DEMO DATA SUMMARY")
        self.stdout.write("="*50)
        
        # Task statistics
        total_tasks = user.tasks.count()
        todo_tasks = user.tasks.filter(status='todo').count()
        in_progress_tasks = user.tasks.filter(status='in_progress').count()
        completed_tasks = user.tasks.filter(status='completed').count()
        
        scheduled_tasks = user.tasks.filter(start_time__isnull=False).count()
        unscheduled_tasks = user.tasks.filter(start_time__isnull=True, status__in=['todo', 'in_progress']).count()
        
        self.stdout.write(f"📋 Tasks: {total_tasks} total")
        self.stdout.write(f"   - To Do: {todo_tasks}")
        self.stdout.write(f"   - In Progress: {in_progress_tasks}")
        self.stdout.write(f"   - Completed: {completed_tasks}")
        self.stdout.write(f"   - Scheduled: {scheduled_tasks}")
        self.stdout.write(f"   - Unscheduled: {unscheduled_tasks}")
        
        # Priority breakdown
        urgent_tasks = user.tasks.filter(priority=4, status__in=['todo', 'in_progress']).count()
        high_tasks = user.tasks.filter(priority=3, status__in=['todo', 'in_progress']).count()
        medium_tasks = user.tasks.filter(priority=2, status__in=['todo', 'in_progress']).count()
        low_tasks = user.tasks.filter(priority=1, status__in=['todo', 'in_progress']).count()
        
        self.stdout.write(f"\n🎯 Active Task Priorities:")
        self.stdout.write(f"   - Urgent (P4): {urgent_tasks}")
        self.stdout.write(f"   - High (P3): {high_tasks}")
        self.stdout.write(f"   - Medium (P2): {medium_tasks}")
        self.stdout.write(f"   - Low (P1): {low_tasks}")
        
        # Time blocks
        time_blocks = user.time_blocks.count()
        recurring_blocks = user.time_blocks.filter(is_recurring=True).count()
        
        self.stdout.write(f"\n⏰ Availability: {time_blocks} time blocks ({recurring_blocks} recurring)")
        
        # Pomodoro sessions
        pomodoro_sessions = PomodoroSession.objects.filter(task__user=user).count()
        completed_sessions = PomodoroSession.objects.filter(task__user=user, status='completed').count()
        
        self.stdout.write(f"\n🍅 Pomodoro: {pomodoro_sessions} sessions ({completed_sessions} completed)")
        
        # Optimization history
        optimization_count = user.optimization_history.count()
        self.stdout.write(f"\n🤖 Optimization History: {optimization_count} runs")
        
        # Notifications
        pending_notifications = TaskNotification.objects.filter(task__user=user, status='pending').count()
        self.stdout.write(f"\n🔔 Notifications: {pending_notifications} pending")
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("🎯 DEMO FEATURES READY:")
        self.stdout.write("="*50)
        self.stdout.write("✅ Kanban Board - Mix of todo/in-progress/completed tasks")
        self.stdout.write("✅ Calendar View - Scheduled and unscheduled tasks")
        self.stdout.write("✅ Auto Scheduler - Unscheduled tasks ready for optimization")
        self.stdout.write("✅ AI Chat - Task data and context available")
        self.stdout.write("✅ Email Notifications - Preferences configured")
        self.stdout.write("✅ PDF Export - Scheduled tasks ready for export")
        self.stdout.write("✅ Pomodoro Timer - Historical sessions available")
        self.stdout.write("✅ Priority Management - Tasks across all priority levels")
        self.stdout.write("✅ Time Tracking - Estimated vs actual hours data")
        self.stdout.write("\n🚀 Your demo environment is ready for presentation!")