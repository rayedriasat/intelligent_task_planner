# Google OAuth 2.0 Setup Guide

This guide will help you set up Google OAuth 2.0 authentication for your Django Task Planner application.

## Prerequisites

1. Python environment with the required packages installed
2. Django application running
3. Google Cloud Console account

## Step 1: Google Cloud Console Setup

1. **Create a Google Cloud Project** (if you don't have one):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Click "Select a project" → "New Project"
   - Enter project name and click "Create"

2. **Enable Google+ API**:
   - In the Google Cloud Console, go to "APIs & Services" → "Library"
   - Search for "Google+ API" and enable it
   - Also enable "Google Identity and Access Management (IAM) API"

3. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Web application"
   - Set the name (e.g., "Task Planner OAuth")
   - Add authorized redirect URIs:
     - `http://127.0.0.1:8000/accounts/google/login/callback/`
     - `http://localhost:8000/accounts/google/login/callback/`
     - Add your production domain when deploying: `https://yourdomain.com/accounts/google/login/callback/`
   - Click "Create"
   - Copy the Client ID and Client Secret

## Step 2: Environment Configuration

1. **Create `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. **Add Google OAuth credentials to `.env`**:
   ```env
   GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
   ```

## Step 3: Database Setup

Run the management command to set up the Google OAuth application in the database:

```bash
python manage.py setup_google_oauth
```

This command will:
- Create a SocialApp entry for Google OAuth
- Associate it with your site
- Display configuration information

## Step 4: Test the Integration

1. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

2. **Test Google OAuth**:
   - Go to `http://127.0.0.1:8000/accounts/login/`
   - You should see a "Continue with Google" button
   - Click it to test the OAuth flow

## Troubleshooting

### Common Issues

1. **"OAuth Error: redirect_uri_mismatch"**
   - Check that your redirect URIs in Google Cloud Console match exactly
   - Make sure you're using the correct domain (127.0.0.1 vs localhost)

2. **"Google+ API not enabled"**
   - Enable the Google+ API in Google Cloud Console
   - Wait a few minutes for the changes to propagate

3. **"Invalid client_id"**
   - Verify your `GOOGLE_OAUTH2_CLIENT_ID` in the `.env` file
   - Check for extra spaces or characters

4. **Social app not found**
   - Run `python manage.py setup_google_oauth` again
   - Check that the SocialApp was created in Django admin

### Debug Steps

1. **Check Django admin**:
   - Go to `/admin/socialaccount/socialapp/`
   - Verify the Google OAuth app exists and has correct credentials

2. **Check site configuration**:
   - Go to `/admin/sites/site/`
   - Ensure the domain matches your development/production domain

3. **Check logs**:
   - Look at Django logs for any OAuth-related errors
   - Check browser console for JavaScript errors

## Production Deployment

When deploying to production:

1. **Update redirect URIs** in Google Cloud Console with your production domain
2. **Set production environment variables**
3. **Update Site domain** in Django admin
4. **Run the setup command** on production server

## Security Considerations

- Keep your `GOOGLE_OAUTH2_CLIENT_SECRET` secure and never commit it to version control
- Use HTTPS in production
- Regularly rotate your OAuth credentials
- Monitor OAuth usage in Google Cloud Console

## Additional Features

The implementation includes:
- Automatic account creation for new Google users
- Email verification disabled for social accounts
- User profile information from Google
- Seamless integration with existing email/password authentication

For more advanced configuration, check the `SOCIALACCOUNT_PROVIDERS` settings in `settings.py`.
