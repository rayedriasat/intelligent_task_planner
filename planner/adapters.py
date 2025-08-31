"""
Custom adapter for Google social account to automatically setup calendar integration.
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.shortcuts import redirect


class GoogleCalendarSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter to handle Google Calendar setup after social login."""
    
    def pre_social_login(self, request, sociallogin):
        """
        Handle pre-social login to connect existing users by email.
        """
        # If user is already authenticated, skip
        if request.user.is_authenticated:
            return
        
        # Only for Google provider
        if sociallogin.account.provider != 'google':
            return
        
        # Try to find existing user by email
        email = sociallogin.account.extra_data.get('email')
        if email:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(email__iexact=email)
                # Connect the social account to existing user
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass  # Will create new user
    
    def save_user(self, request, sociallogin, form=None):
        """Override to set up Google Calendar integration after user creation."""
        user = super().save_user(request, sociallogin, form)
        
        # Check if this is a Google login
        if sociallogin.account.provider == 'google':
            self._setup_google_calendar_integration(user, request)
        
        return user
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """Handle authentication errors gracefully."""
        if provider_id == 'google':
            messages.error(
                request, 
                'Google authentication failed. Please try again or contact support if the issue persists.'
            )
        return super().authentication_error(request, provider_id, error, exception, extra_context)
    
    def _setup_google_calendar_integration(self, user, request):
        """Set up basic Google Calendar integration for new Google users."""
        try:
            from planner.models import GoogleCalendarIntegration
            from planner.services.google_calendar_service import GoogleCalendarService
            
            # Create or get integration settings
            integration, created = GoogleCalendarIntegration.objects.get_or_create(
                user=user,
                defaults={
                    'is_enabled': True,
                    'sync_direction': 'both',
                }
            )
            
            if created or not integration.google_calendar_id:
                try:
                    # Try to get the primary calendar ID
                    service = GoogleCalendarService(user)
                    primary_calendar_id = service.get_primary_calendar()
                    integration.google_calendar_id = primary_calendar_id
                    integration.save()
                    
                    messages.success(
                        request,
                        'Google Calendar integration set up successfully! You can now sync your tasks.'
                    )
                except Exception as e:
                    # If calendar setup fails, still create the integration but disabled
                    integration.is_enabled = False
                    integration.save()
                    
                    messages.warning(
                        request,
                        'Google login successful, but calendar setup needs attention. '
                        'Please visit Google Calendar settings to complete setup.'
                    )
                    
        except Exception as e:
            # Don't break the login process if calendar setup fails
            messages.info(
                request,
                'Google login successful! Visit Google Calendar settings to enable calendar sync.'
            )
