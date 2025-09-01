# Pre-Deployment Checklist

Use this checklist to ensure your deployment goes smoothly.

## Before You Start

- [ ] Have a PythonAnywhere account ready
- [ ] Choose your MySQL hosting provider
- [ ] Have your Google OAuth credentials ready
- [ ] Have your email credentials for notifications

## Database Setup

- [ ] Created free MySQL database
- [ ] Noted down database credentials:
  - [ ] Database name
  - [ ] Username  
  - [ ] Password
  - [ ] Host
  - [ ] Port (usually 3306)

## Environment Variables

- [ ] Generated new SECRET_KEY using `python generate_secret_key.py`
- [ ] Set DEBUG=False
- [ ] Configured database settings
- [ ] Set up Google OAuth credentials
- [ ] Configured email settings
- [ ] Set OpenRouter API key (if using AI features)

## Files to Update

- [ ] Update `intelligent_task_planner/production_settings.py` with your username
- [ ] Update `wsgi_production.py` with your username
- [ ] Create `.env` file from `env_example.txt`

## PythonAnywhere Configuration

- [ ] Uploaded project files
- [ ] Created virtual environment
- [ ] Installed production requirements
- [ ] Configured web app settings
- [ ] Set up static file mappings
- [ ] Configured WSGI file

## Database Migration

- [ ] Ran database migrations
- [ ] Created superuser account
- [ ] Collected static files

## Google OAuth Setup

- [ ] Created Google Cloud project
- [ ] Enabled Calendar API
- [ ] Created OAuth credentials
- [ ] Added PythonAnywhere domain to authorized domains
- [ ] Added redirect URIs

## Testing

- [ ] Website loads successfully
- [ ] User registration works
- [ ] User login works
- [ ] Google OAuth works
- [ ] Admin panel accessible
- [ ] Static files load correctly

## Security

- [ ] Used strong passwords
- [ ] Never committed .env file
- [ ] Verified all sensitive data uses environment variables
- [ ] Tested in production mode (DEBUG=False)

## Optional

- [ ] Set up Django-Q2 scheduled task
- [ ] Configured email notifications
- [ ] Set up monitoring/logging

## Post-Deployment

- [ ] Test all major features
- [ ] Monitor error logs
- [ ] Check performance
- [ ] Set up regular backups (if needed)
