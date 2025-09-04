# Generated manually

from django.db import migrations


def populate_completed_at(apps, schema_editor):
    """Populate completed_at field for existing completed tasks using updated_at as fallback."""
    Task = apps.get_model('planner', 'Task')
    
    # Update all completed tasks that don't have a completed_at timestamp
    completed_tasks = Task.objects.filter(status='completed', completed_at__isnull=True)
    
    for task in completed_tasks:
        # Use updated_at as the completion time for existing completed tasks
        task.completed_at = task.updated_at
        task.save()
    
    print(f"Updated {completed_tasks.count()} completed tasks with completion timestamps")


def reverse_populate_completed_at(apps, schema_editor):
    """Reverse the migration by clearing completed_at field."""
    Task = apps.get_model('planner', 'Task')
    Task.objects.filter(status='completed').update(completed_at=None)


class Migration(migrations.Migration):
    dependencies = [
        ('planner', '0012_task_completed_at'),
    ]

    operations = [
        migrations.RunPython(populate_completed_at, reverse_populate_completed_at),
    ]