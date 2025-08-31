from django.core.management.base import BaseCommand
from planner.models import CalendarSyncLog

class Command(BaseCommand):
    help = 'Clear failed sync entries with 0 events'

    def handle(self, *args, **options):
        # Delete sync logs that failed with 0 events (the problematic ones)
        failed_syncs = CalendarSyncLog.objects.filter(
            events_synced=0,
            status='failed'
        )
        
        count = failed_syncs.count()
        failed_syncs.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} failed sync entries with 0 events')
        )
        
        # Show remaining sync logs
        remaining = CalendarSyncLog.objects.all().order_by('-timestamp')[:5]
        self.stdout.write("\nRemaining sync logs:")
        for log in remaining:
            self.stdout.write(f"- {log.get_sync_type_display()}: {log.status} - {log.events_synced} events")
