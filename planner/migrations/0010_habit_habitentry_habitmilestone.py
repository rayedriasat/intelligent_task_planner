# Generated manually for habit tracking models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('planner', '0009_canvasannouncement_canvasassignment_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Habit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='What habit do you want to track?', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Additional details about your habit', null=True)),
                ('category', models.CharField(choices=[('health', 'Health & Fitness'), ('learning', 'Learning & Education'), ('productivity', 'Productivity'), ('mindfulness', 'Mindfulness & Mental Health'), ('social', 'Social & Relationships'), ('hobbies', 'Hobbies & Recreation'), ('work', 'Work & Career'), ('finance', 'Finance'), ('other', 'Other')], default='other', max_length=20)),
                ('target_frequency', models.CharField(choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='daily', max_length=10)),
                ('target_count', models.PositiveIntegerField(default=1, help_text='How many times per frequency period?')),
                ('unit', models.CharField(blank=True, help_text='Unit of measurement (e.g., minutes, pages, cups)', max_length=50)),
                ('goal_description', models.TextField(blank=True, help_text='Why is this habit important to you?', null=True)),
                ('target_streak', models.PositiveIntegerField(blank=True, help_text='Target streak (optional)', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('color', models.CharField(default='#3B82F6', help_text='Hex color code for habit visualization', max_length=7)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='habits', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='HabitMilestone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('milestone_type', models.CharField(choices=[('streak', 'Streak Milestone'), ('total', 'Total Completions'), ('consistency', 'Consistency Achievement'), ('custom', 'Custom Milestone')], max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('target_value', models.PositiveIntegerField(help_text='Target value to achieve (days, count, etc.)')),
                ('is_achieved', models.BooleanField(default=False)),
                ('achieved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('habit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='milestones', to='planner.habit')),
            ],
            options={
                'ordering': ['-achieved_at', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='HabitEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(help_text='Date when the habit was performed')),
                ('is_completed', models.BooleanField(default=False)),
                ('count', models.PositiveIntegerField(default=0, help_text='How many times the habit was performed')),
                ('notes', models.TextField(blank=True, help_text='Optional notes about this entry', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('habit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='planner.habit')),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.AddIndex(
            model_name='habit',
            index=models.Index(fields=['user', 'is_active'], name='planner_hab_user_id_b93a3a_idx'),
        ),
        migrations.AddIndex(
            model_name='habit',
            index=models.Index(fields=['user', 'category'], name='planner_hab_user_id_dd2e5b_idx'),
        ),
        migrations.AddIndex(
            model_name='habit',
            index=models.Index(fields=['user', 'target_frequency'], name='planner_hab_user_id_02a3f3_idx'),
        ),
        migrations.AddIndex(
            model_name='habitmilestone',
            index=models.Index(fields=['habit', 'milestone_type'], name='planner_hab_habit_i_89cf45_idx'),
        ),
        migrations.AddIndex(
            model_name='habitmilestone',
            index=models.Index(fields=['habit', 'is_achieved'], name='planner_hab_habit_i_8b4c3e_idx'),
        ),
        migrations.AddIndex(
            model_name='habitentry',
            index=models.Index(fields=['habit', 'date'], name='planner_hab_habit_i_bd3fe8_idx'),
        ),
        migrations.AddIndex(
            model_name='habitentry',
            index=models.Index(fields=['habit', 'is_completed'], name='planner_hab_habit_i_3e2a1c_idx'),
        ),
        migrations.AddIndex(
            model_name='habitentry',
            index=models.Index(fields=['date', 'is_completed'], name='planner_hab_date_85a242_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='habitentry',
            unique_together={('habit', 'date')},
        ),
    ]