"""
Management command to set up Google OAuth 2.0 application.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Set up Google OAuth 2.0 application'

    def handle(self, *args, **options):
        client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
        client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET

        if not client_id or not client_secret:
            self.stdout.write(
                self.style.ERROR(
                    'Google OAuth credentials not found in environment variables.\n'
                    'Please set GOOGLE_OAUTH2_CLIENT_ID and GOOGLE_OAUTH2_CLIENT_SECRET in your .env file.'
                )
            )
            return

        # Get or create the default site
        site = Site.objects.get_current()

        # Create or update Google OAuth app
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google OAuth',
                'client_id': client_id,
                'secret': client_secret,
            }
        )

        if not created:
            google_app.client_id = client_id
            google_app.secret = client_secret
            google_app.save()

        # Add the site to the app
        google_app.sites.add(site)

        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} Google OAuth application successfully!\n'
                f'Provider: {google_app.provider}\n'
                f'Client ID: {client_id[:20]}...\n'
                f'Site: {site.domain}'
            )
        )

        if created:
            self.stdout.write(
                self.style.WARNING(
                    '\nDon\'t forget to:\n'
                    '1. Set up your Google OAuth app in Google Cloud Console\n'
                    '2. Add authorized redirect URIs:\n'
                    f'   - http://{site.domain}/accounts/google/login/callback/\n'
                    f'   - https://{site.domain}/accounts/google/login/callback/\n'
                    '3. Enable Google+ API (if using profile information)'
                )
            )
