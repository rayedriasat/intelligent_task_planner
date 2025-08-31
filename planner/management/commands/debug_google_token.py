from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp


class Command(BaseCommand):
    help = 'Manually create a test Google token for debugging'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email of the user to create token for',
        )

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(f"❌ User {email} not found")
            return
        
        try:
            social_account = SocialAccount.objects.get(user=user, provider='google')
        except SocialAccount.DoesNotExist:
            self.stdout.write(f"❌ No Google social account found for {email}")
            return
        
        try:
            google_app = SocialApp.objects.get(provider='google')
        except SocialApp.DoesNotExist:
            self.stdout.write(f"❌ No Google social app configured")
            return
        
        # Check if token already exists
        existing_token = SocialToken.objects.filter(
            account=social_account,
            app=google_app
        ).first()
        
        if existing_token:
            self.stdout.write(f"✅ Token already exists: {existing_token.token[:20]}...")
            return
        
        # For debugging, create a dummy token
        # In real scenario, this would come from Google OAuth flow
        self.stdout.write(f"⚠️  No real token available - user needs to re-authenticate")
        self.stdout.write(f"   The OAuth flow should automatically create tokens")
        self.stdout.write(f"   Visit: http://localhost:8000/accounts/google/login/")
        self.stdout.write(f"   Make sure to grant calendar permissions!")
        
        # Show debugging info
        self.stdout.write(f"\n🔍 Debug Info:")
        self.stdout.write(f"   User: {user.email}")
        self.stdout.write(f"   Social Account UID: {social_account.uid}")
        self.stdout.write(f"   Google App Client ID: {google_app.client_id[:10]}...")
        self.stdout.write(f"   Sites configured: {[s.domain for s in google_app.sites.all()]}")
        
        # Check settings
        from django.conf import settings
        self.stdout.write(f"\n⚙️  Settings Check:")
        self.stdout.write(f"   SOCIALACCOUNT_STORE_TOKENS: {getattr(settings, 'SOCIALACCOUNT_STORE_TOKENS', 'Not set')}")
        self.stdout.write(f"   Calendar scope in SOCIALACCOUNT_PROVIDERS: {'https://www.googleapis.com/auth/calendar' in settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('SCOPE', [])}")
        self.stdout.write(f"   access_type=offline: {settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('AUTH_PARAMS', {}).get('access_type') == 'offline'}")
