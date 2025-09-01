"""
Production settings for PythonAnywhere deployment
"""
from .settings import *
import os

# Production settings
DEBUG = False

# Add your PythonAnywhere domain here
ALLOWED_HOSTS = [
    'yourusername.pythonanywhere.com',  # Replace 'yourusername' with your actual username
    'www.yourusername.pythonanywhere.com',
    '127.0.0.1',
    'localhost',
]

# Database configuration for production
# You'll need to update these with your actual database credentials
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# Static files configuration for PythonAnywhere
STATIC_URL = '/static/'
STATIC_ROOT = '/home/yourusername/intelligent_task_planner/staticfiles'  # Update with your username

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/yourusername/intelligent_task_planner/media'  # Update with your username

# Security settings for production
SECURE_SSL_REDIRECT = False  # PythonAnywhere handles SSL
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/home/yourusername/intelligent_task_planner/logs/django.log',  # Update with your username
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'planner': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email configuration (you may want to use a service like SendGrid for production)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Django-Q2 configuration for production
Q_CLUSTER = {
    'name': 'task_planner_prod',
    'workers': 1,  # Reduced for free tier
    'recycle': 500,
    'timeout': 30,  # Reduced timeout
    'compress': True,
    'save_limit': 100,  # Reduced for free tier
    'queue_limit': 200,  # Reduced for free tier
    'cpu_affinity': 1,
    'label': 'Django Q2 Production',
    'orm': 'default'
}
