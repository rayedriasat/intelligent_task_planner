from django.core.management.base import BaseCommand
from django.db.models import Count
from planner.models import CalendarSyncLog
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Remove duplicate sync entries that occurred within the same minute'

    def handle(self, *args, **options):
        # Find and remove duplicate entries that happened within 1 minute of each other
        # with the same event count
        
        duplicates_removed = 0
        
        # Get all sync logs ordered by timestamp
        sync_logs = CalendarSyncLog.objects.all().order_by('-timestamp')
        
        # Group by user and look for duplicates within 1 minute
        processed = set()
        
        for log in sync_logs:
            if log.id in processed:
                continue
                
            # Find other logs from same user within 1 minute with same event count
            time_window = timedelta(minutes=1)
            similar_logs = CalendarSyncLog.objects.filter(
                user=log.user,
                events_synced=log.events_synced,
                timestamp__gte=log.timestamp - time_window,
                timestamp__lte=log.timestamp + time_window
            ).order_by('timestamp')
            
            if similar_logs.count() > 1:
                # Keep the first one, delete the rest
                first_log = similar_logs.first()
                duplicates = similar_logs.exclude(id=first_log.id)
                
                for dup in duplicates:
                    processed.add(dup.id)
                    
                count = duplicates.count()
                duplicates.delete()
                duplicates_removed += count
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully removed {duplicates_removed} duplicate sync entries')
        )
        
        # Show remaining sync logs
        remaining = CalendarSyncLog.objects.all().order_by('-timestamp')[:5]
        self.stdout.write("\nRemaining sync logs:")
        for log in remaining:
            self.stdout.write(f"- {log.get_sync_type_display()}: {log.status} - {log.events_synced} events ({log.timestamp})")
