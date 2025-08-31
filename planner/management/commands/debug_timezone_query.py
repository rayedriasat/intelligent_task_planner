from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from planner.models import Task
from datetime import datetime, timedelta
from django.utils import timezone
import pytz


class Command(BaseCommand):
    help = 'Debug timezone conversion in task queries'

    def handle(self, *args, **options):
        user = User.objects.first()
        
        # Get the tasks 
        all_scheduled = user.tasks.filter(start_time__isnull=False)
        
        self.stdout.write(f"Timezone debugging:")
        self.stdout.write(f"Current timezone: {timezone.get_current_timezone()}")
        
        for task in all_scheduled:
            self.stdout.write(f"\nTask: {task.title}")
            self.stdout.write(f"  Raw start_time: {task.start_time}")
            self.stdout.write(f"  start_time.date(): {task.start_time.date()}")
            
            # Convert to local timezone and check date
            local_time = timezone.localtime(task.start_time)
            self.stdout.write(f"  Local time: {local_time}")
            self.stdout.write(f"  Local date: {local_time.date()}")
            
            # Test the actual database query
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT start_time FROM planner_task WHERE id = %s", 
                    [task.id]
                )
                db_time = cursor.fetchone()[0]
                self.stdout.write(f"  Database time: {db_time}")
        
        # Test the problematic query step by step
        self.stdout.write(f"\nTesting date filtering:")
        
        import datetime as dt
        test_date = dt.date(2025, 8, 31)
        
        # Try different query approaches
        query1 = user.tasks.filter(start_time__date=test_date)
        self.stdout.write(f"Query 1 (start_time__date=test_date): {query1.count()}")
        
        # Use timezone-aware datetime range
        start_of_day = timezone.make_aware(datetime.combine(test_date, datetime.min.time()))
        end_of_day = timezone.make_aware(datetime.combine(test_date, datetime.max.time()))
        
        query2 = user.tasks.filter(start_time__gte=start_of_day, start_time__lte=end_of_day)
        self.stdout.write(f"Query 2 (datetime range): {query2.count()}")
        
        # Try with different timezone
        utc = pytz.UTC
        start_utc = utc.localize(datetime.combine(test_date, datetime.min.time()))
        end_utc = utc.localize(datetime.combine(test_date, datetime.max.time()))
        
        query3 = user.tasks.filter(start_time__gte=start_utc, start_time__lte=end_utc)
        self.stdout.write(f"Query 3 (UTC datetime range): {query3.count()}")
        
        # Check what the SQL actually looks like
        self.stdout.write(f"\nSQL for date query:")
        self.stdout.write(str(query1.query))
