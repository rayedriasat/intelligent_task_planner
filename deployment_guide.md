# Deployment Guide: Hosting Your Intelligent Task Planner for Free

This guide will help you deploy your Django application to PythonAnywhere with a free MySQL database.

## Step 1: Set Up Free MySQL Database

### Option 1: PlanetScale (Recommended)
1. Go to [PlanetScale](https://planetscale.com/)
2. Sign up for a free account
3. Create a new database
4. Get your connection details from the dashboard
5. Note down: HOST, USERNAME, PASSWORD, DATABASE_NAME

### Option 2: Railway
1. Go to [Railway](https://railway.app/)
2. Sign up and create a new project
3. Add a MySQL database service
4. Get connection details from the database service

### Option 3: db4free.net (Limited but truly free)
1. Go to [db4free.net](https://www.db4free.net/)
2. Create a free MySQL database (200MB limit)
3. Note down your credentials

## Step 2: Set Up PythonAnywhere Account

1. Go to [PythonAnywhere](https://www.pythonanywhere.com/)
2. Sign up for a free "Beginner" account
3. Note your username (you'll need it for configuration)

## Step 3: Upload Your Project

### Method 1: Git (Recommended)
1. In PythonAnywhere console, run:
```bash
git clone https://github.com/Rayed/intelligent_task_planner.git
cd intelligent_task_planner
```

### Method 2: Upload Files
1. Use the "Files" tab in PythonAnywhere dashboard
2. Upload your project files

## Step 4: Install Dependencies

1. Open a Bash console in PythonAnywhere
2. Navigate to your project directory:
```bash
cd ~/intelligent_task_planner
```

3. Create a virtual environment:
```bash
python3.10 -m venv venv
source venv/bin/activate
```

4. Install requirements:
```bash
pip install -r requirements.txt
```

## Step 5: Configure Environment Variables

1. Create a `.env` file in your project root:
```bash
nano .env
```

2. Add your environment variables (use the env_example.txt as reference):
```
SECRET_KEY=your-generated-secret-key
DEBUG=False
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
DB_PORT=3306
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Step 6: Update Configuration Files

1. Edit `intelligent_task_planner/production_settings.py`:
   - Replace `yourusername` with your PythonAnywhere username
   - Update paths accordingly

2. Edit `wsgi_production.py`:
   - Replace `yourusername` with your PythonAnywhere username

## Step 7: Set Up Database

1. Run migrations:
```bash
python manage.py migrate --settings=intelligent_task_planner.production_settings
```

2. Create a superuser:
```bash
python manage.py createsuperuser --settings=intelligent_task_planner.production_settings
```

3. Collect static files:
```bash
python manage.py collectstatic --settings=intelligent_task_planner.production_settings
```

## Step 8: Configure Web App in PythonAnywhere

1. Go to the "Web" tab in your PythonAnywhere dashboard
2. Click "Add a new web app"
3. Choose "Manual configuration" and Python 3.10
4. Set the following:

### Source code:
```
/home/Rayed/intelligent_task_planner
```

### Working directory:
```
/home/Rayed/intelligent_task_planner
```

### WSGI configuration file:
```
/home/Rayed/intelligent_task_planner/wsgi_production.py
```

### Virtual environment:
```
/home/Rayed/intelligent_task_planner/venv
```

## Step 9: Configure Static Files

In the "Web" tab, add these static file mappings:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/Rayed/intelligent_task_planner/staticfiles/` |
| `/media/` | `/home/Rayed/intelligent_task_planner/media/` |

## Step 10: Set Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API and Google+ API
4. Create OAuth 2.0 credentials
5. Add your PythonAnywhere domain to authorized domains:
   - `Rayed.pythonanywhere.com`
6. Add redirect URIs:
   - `https://Rayed.pythonanywhere.com/accounts/google/login/callback/`

## Step 11: Test Your Deployment

1. Click "Reload" in the Web tab
2. Visit `https://Rayed.pythonanywhere.com`
3. Test user registration and login
4. Test Google Calendar integration

## Step 12: Set Up Scheduled Tasks (Optional)

For Django-Q2 task processing:
1. Go to the "Tasks" tab in PythonAnywhere
2. Create a new scheduled task:
   - Command: `/home/Rayed/intelligent_task_planner/venv/bin/python /home/Rayed/intelligent_task_planner/manage.py qcluster --settings=intelligent_task_planner.production_settings`
   - Hour: Leave blank (runs continuously)
   - Minute: Leave blank

## Troubleshooting

### Common Issues:

1. **Database Connection Error**: Check your database credentials in `.env`
2. **Static Files Not Loading**: Ensure static file mappings are correct
3. **Google OAuth Error**: Verify redirect URIs and domain settings
4. **Import Errors**: Make sure virtual environment is activated and requirements installed

### Logs:
- Check error logs in PythonAnywhere Web tab
- Check Django logs in `/home/Rayed/intelligent_task_planner/logs/`

## Free Tier Limitations

### PythonAnywhere Free Tier:
- 512MB disk space
- 1 web app
- HTTP only (no HTTPS on free tier)
- Limited CPU time

### Tips for Free Tier:
- Optimize your code for minimal resource usage
- Use efficient database queries
- Consider upgrading if you need more resources

## Security Notes

1. Always use environment variables for sensitive data
2. Never commit `.env` files to version control
3. Regularly update dependencies
4. Use strong passwords for database and admin accounts

## Need Help?

- PythonAnywhere Help: https://help.pythonanywhere.com/
- Django Documentation: https://docs.djangoproject.com/
- Your app logs in PythonAnywhere dashboard

Good luck with your deployment! 🚀
