from django.core.management.base import BaseCommand
from django.utils import timezone
from planner.models import Task
import pytz


class Command(BaseCommand):
    help = 'Convert existing task times from UTC to local timezone'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🔄 Converting task times from UTC to local timezone")
        if dry_run:
            self.stdout.write("🔍 DRY RUN - No changes will be made")
        self.stdout.write("=" * 60)
        
        # Get current timezone
        current_tz = timezone.get_current_timezone()
        utc_tz = pytz.UTC
        
        self.stdout.write(f"Current timezone: {current_tz}")
        
        # Find tasks with start_time in UTC
        tasks_with_utc_times = Task.objects.filter(
            start_time__isnull=False
        )
        
        self.stdout.write(f"Found {tasks_with_utc_times.count()} tasks with start times")
        
        converted_count = 0
        
        for task in tasks_with_utc_times:
            old_start = task.start_time
            old_end = task.end_time
            
            # Check if the time appears to be in UTC (has +00:00 offset)
            if old_start.tzinfo == utc_tz or '+00:00' in str(old_start):
                # Convert to local timezone
                new_start = old_start.astimezone(current_tz)
                new_end = old_end.astimezone(current_tz) if old_end else None
                
                self.stdout.write(f"\n📋 Task: {task.title}")
                self.stdout.write(f"   Old start: {old_start}")
                self.stdout.write(f"   New start: {new_start}")
                
                if old_end:
                    self.stdout.write(f"   Old end: {old_end}")
                    self.stdout.write(f"   New end: {new_end}")
                
                if not dry_run:
                    task.start_time = new_start
                    if old_end:
                        task.end_time = new_end
                    task.save()
                    self.stdout.write("   ✅ Converted")
                else:
                    self.stdout.write("   🔍 Would convert")
                
                converted_count += 1
            else:
                self.stdout.write(f"\n📋 Task: {task.title}")
                self.stdout.write(f"   Start: {old_start}")
                self.stdout.write("   ℹ️  Already in local timezone, skipping")
        
        if converted_count > 0:
            if not dry_run:
                self.stdout.write(f"\n✅ Converted {converted_count} tasks to local timezone")
                self.stdout.write("   Tasks should now appear on correct dates in Google Calendar")
            else:
                self.stdout.write(f"\n🔍 Would convert {converted_count} tasks")
                self.stdout.write("   Run without --dry-run to apply changes")
        else:
            self.stdout.write(f"\n✅ No tasks needed conversion")
        
        self.stdout.write(f"\n💡 Note: New tasks will automatically use the correct timezone")
