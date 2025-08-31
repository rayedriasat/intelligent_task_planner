from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialToken


class Command(BaseCommand):
    help = 'Clear Google social account for a user to allow fresh authentication'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email of the user to clear Google account for',
        )

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(f"❌ User with email {email} not found")
            return
        
        # Remove social accounts
        social_accounts = SocialAccount.objects.filter(user=user, provider='google')
        count = social_accounts.count()
        
        if count > 0:
            social_accounts.delete()
            self.stdout.write(f"✅ Removed {count} Google social account(s) for {email}")
        else:
            self.stdout.write(f"ℹ️  No Google social accounts found for {email}")
        
        # Remove any orphaned tokens
        SocialToken.objects.filter(account__user=user, account__provider='google').delete()
        
        self.stdout.write(f"✅ User {email} can now authenticate fresh with Google")
        self.stdout.write(f"   Visit: http://localhost:8000/accounts/google/login/")
