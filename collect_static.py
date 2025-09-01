#!/usr/bin/env python3
"""
Script to collect static files for production deployment.
Run this after uploading your project to PythonAnywhere.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intelligent_task_planner.production_settings')
    django.setup()
    
    print("Collecting static files for production...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    print("Static files collected successfully!")
