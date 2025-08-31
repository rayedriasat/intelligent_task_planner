from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp
from planner.models import GoogleCalendarIntegration


class Command(BaseCommand):
    help = 'Fix Google Calendar integration for existing users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user to fix integration for',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        
        if email:
            users = User.objects.filter(email=email)
        else:
            users = User.objects.filter(socialaccount__provider='google')
        
        self.stdout.write(f"Found {users.count()} users with Google accounts")
        
        for user in users:
            self.stdout.write(f"\nProcessing user: {user.email}")
            
            # Check social account
            social_accounts = SocialAccount.objects.filter(user=user, provider='google')
            if not social_accounts.exists():
                self.stdout.write(f"  ❌ No Google social account found")
                continue
                
            social_account = social_accounts.first()
            self.stdout.write(f"  ✅ Google social account found (ID: {social_account.uid})")
            
            # Check social token
            google_app = SocialApp.objects.filter(provider='google').first()
            if not google_app:
                self.stdout.write(f"  ❌ No Google social app configured")
                continue
                
            social_tokens = SocialToken.objects.filter(
                account=social_account,
                app=google_app
            )
            
            if not social_tokens.exists():
                self.stdout.write(f"  ❌ No Google social token found - user needs to re-authenticate")
                self.stdout.write(f"      Visit: http://localhost:8000/accounts/google/login/ to re-authenticate")
            else:
                token = social_tokens.first()
                self.stdout.write(f"  ✅ Google social token found")
                self.stdout.write(f"      Token (first 20 chars): {token.token[:20]}...")
                if token.token_secret:
                    self.stdout.write(f"      Refresh token available: Yes")
                else:
                    self.stdout.write(f"      Refresh token available: No")
            
            # Check Google Calendar integration
            integration, created = GoogleCalendarIntegration.objects.get_or_create(
                user=user,
                defaults={
                    'is_enabled': True,
                    'sync_direction': 'both',
                }
            )
            
            if created:
                self.stdout.write(f"  ✅ Created Google Calendar integration")
            else:
                self.stdout.write(f"  ✅ Google Calendar integration exists (enabled: {integration.is_enabled})")
                if not integration.is_enabled:
                    integration.is_enabled = True
                    integration.save()
                    self.stdout.write(f"  ✅ Enabled Google Calendar integration")
            
            self.stdout.write(f"  📊 Integration status: {'Active' if social_tokens.exists() and integration.is_enabled else 'Inactive'}")
