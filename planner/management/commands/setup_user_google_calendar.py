"""
Management command to set up Google Calendar integration for a specific user.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from planner.models import GoogleCalendarIntegration
from allauth.socialaccount.models import SocialToken


class Command(BaseCommand):
    help = 'Set up Google Calendar integration for a user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address of the user to set up Google Calendar for',
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Set up Google Calendar for all users with Google OAuth tokens',
        )

    def handle(self, *args, **options):
        if options['all_users']:
            self.setup_for_all_users()
        elif options['email']:
            self.setup_for_user(options['email'])
        else:
            self.stdout.write(
                self.style.ERROR(
                    'Please specify either --email <email> or --all-users'
                )
            )

    def setup_for_user(self, email):
        """Set up Google Calendar integration for a specific user."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} not found.')
            )
            return

        self._setup_calendar_integration(user)

    def setup_for_all_users(self):
        """Set up Google Calendar integration for all users with Google tokens."""
        # Get all users who have Google social tokens
        google_tokens = SocialToken.objects.filter(
            account__provider='google'
        ).select_related('account__user')
        
        users_with_google = set(token.account.user for token in google_tokens)
        
        self.stdout.write(
            f'Found {len(users_with_google)} users with Google accounts.'
        )
        
        for user in users_with_google:
            self._setup_calendar_integration(user)

    def _setup_calendar_integration(self, user):
        """Set up Google Calendar integration for a user."""
        try:
            # Check if user has Google OAuth token
            google_token = SocialToken.objects.filter(
                account__user=user,
                account__provider='google'
            ).first()
            
            if not google_token:
                self.stdout.write(
                    self.style.WARNING(
                        f'User {user.email} does not have a Google OAuth token. Skipping.'
                    )
                )
                return

            with transaction.atomic():
                # Create or get integration
                integration, created = GoogleCalendarIntegration.objects.get_or_create(
                    user=user,
                    defaults={
                        'is_enabled': True,
                        'sync_direction': 'both',
                    }
                )

                if created:
                    action = 'Created'
                else:
                    action = 'Updated'
                    integration.is_enabled = True
                    integration.sync_direction = 'both'

                # Try to get primary calendar ID
                try:
                    from planner.services.google_calendar_service import GoogleCalendarService
                    service = GoogleCalendarService(user)
                    primary_calendar_id = service.get_primary_calendar()
                    integration.google_calendar_id = primary_calendar_id
                    integration.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'{action} Google Calendar integration for {user.email} '
                            f'with calendar ID: {primary_calendar_id[:30]}...'
                        )
                    )
                    
                except Exception as e:
                    integration.is_enabled = False
                    integration.save()
                    
                    self.stdout.write(
                        self.style.WARNING(
                            f'{action} Google Calendar integration for {user.email} '
                            f'but could not access calendar: {str(e)}'
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error setting up Google Calendar for {user.email}: {str(e)}'
                )
            )
