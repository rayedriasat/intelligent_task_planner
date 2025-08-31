from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialToken, SocialAccount, SocialApp


class Command(BaseCommand):
    help = 'Test Google Calendar API connectivity and token validation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user to test Google Calendar for',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                self.stdout.write(f"❌ User with email {email} not found")
                return
        else:
            # Find any user with Google tokens
            users_with_tokens = User.objects.filter(
                socialaccount__provider='google',
                socialaccount__socialtoken__isnull=False
            ).distinct()
            
            if not users_with_tokens.exists():
                self.stdout.write("❌ No users found with Google tokens")
                self.stdout.write("   Please authenticate with Google first at: http://localhost:8000/accounts/google/login/")
                return
            
            user = users_with_tokens.first()
            self.stdout.write(f"Testing with user: {user.email}")

        # Check social account
        try:
            social_account = SocialAccount.objects.get(user=user, provider='google')
            self.stdout.write(f"✅ Google social account found (UID: {social_account.uid})")
        except SocialAccount.DoesNotExist:
            self.stdout.write(f"❌ No Google social account found for {user.email}")
            return

        # Check social token
        try:
            google_app = SocialApp.objects.get(provider='google')
            social_token = SocialToken.objects.get(account=social_account, app=google_app)
            self.stdout.write(f"✅ Google social token found")
            self.stdout.write(f"   Token (first 20 chars): {social_token.token[:20]}...")
            
            if social_token.token_secret:
                self.stdout.write(f"   Refresh token: Available")
            else:
                self.stdout.write(f"   Refresh token: ❌ Missing (may cause issues)")
                
        except SocialToken.DoesNotExist:
            self.stdout.write(f"❌ No Google social token found")
            self.stdout.write(f"   Please re-authenticate at: http://localhost:8000/accounts/google/login/")
            return

        # Test Google Calendar service
        try:
            from planner.services.google_calendar_service import GoogleCalendarService
            
            self.stdout.write(f"\n🔧 Testing Google Calendar API...")
            service = GoogleCalendarService(user)
            
            # Test basic API connectivity
            calendar_id = service.get_primary_calendar()
            self.stdout.write(f"✅ Primary calendar ID: {calendar_id}")
            
            # Test calendar access (simple check)
            try:
                # Try to get calendar info using the service directly
                calendar_info = service.service.calendars().get(calendarId='primary').execute()
                self.stdout.write(f"✅ Calendar access confirmed: {calendar_info.get('summary', 'Primary')}")
            except Exception as e:
                self.stdout.write(f"⚠️  Calendar access test failed: {e}")
            
            # Test calendar sync capability
            from planner.models import GoogleCalendarIntegration
            integration, created = GoogleCalendarIntegration.objects.get_or_create(
                user=user,
                defaults={
                    'is_enabled': True,
                    'sync_direction': 'both',
                    'google_calendar_id': calendar_id
                }
            )
            
            if created:
                self.stdout.write(f"✅ Created Google Calendar integration")
            else:
                self.stdout.write(f"✅ Google Calendar integration exists")
                if not integration.google_calendar_id:
                    integration.google_calendar_id = calendar_id
                    integration.save()
                    self.stdout.write(f"✅ Updated calendar ID")
            
            self.stdout.write(f"\n🎉 Google Calendar integration is working!")
            self.stdout.write(f"   Status: {'Active' if integration.is_enabled else 'Inactive'}")
            self.stdout.write(f"   Calendar ID: {integration.google_calendar_id}")
            self.stdout.write(f"   Sync Direction: {integration.sync_direction}")
            
        except Exception as e:
            self.stdout.write(f"❌ Google Calendar API test failed: {str(e)}")
            self.stdout.write(f"   This might be due to:")
            self.stdout.write(f"   1. Missing calendar scope in OAuth token")
            self.stdout.write(f"   2. Invalid or expired token")
            self.stdout.write(f"   3. Google API credentials issue")
            self.stdout.write(f"   Please re-authenticate at: http://localhost:8000/accounts/google/login/")
