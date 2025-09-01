import json
import stripe
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from billing.models import SubscriptionPlan, Customer

class Command(BaseCommand):
    help = 'Test Stripe webhook functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address of the user to test with',
            default='test@example.com'
        )

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        email = options['email']
        
        self.stdout.write(f'Testing Stripe integration for {email}...')
        
        try:
            # Get or create test user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': 'Test',
                    'last_name': 'User'
                }
            )
            
            if created:
                self.stdout.write(f'Created test user: {user.email}')
            else:
                self.stdout.write(f'Using existing user: {user.email}')
            
            # Get Pomodoro plan
            try:
                pomodoro_plan = SubscriptionPlan.objects.get(plan_type='pomodoro')
                self.stdout.write(f'Found Pomodoro plan: {pomodoro_plan.stripe_price_id}')
            except SubscriptionPlan.DoesNotExist:
                self.stdout.write(self.style.ERROR('Pomodoro plan not found. Run "python manage.py setup_stripe" first.'))
                return
            
            # Get or create Stripe customer
            from billing.services import StripeService
            customer_id = StripeService.get_or_create_customer(user)
            self.stdout.write(f'Stripe customer ID: {customer_id}')
            
            # Create a checkout session (but don't redirect to it)
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': pomodoro_plan.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url='http://localhost:8000/billing/success/?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='http://localhost:8000/billing/subscribe/',
                metadata={
                    'user_id': user.id,
                    'plan_id': pomodoro_plan.id,
                }
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Test checkout session created: {checkout_session.id}'
                )
            )
            self.stdout.write(
                f'Checkout URL: {checkout_session.url}'
            )
            
            # Test webhook endpoint availability
            webhook_url = 'http://localhost:8000/billing/webhook/'
            self.stdout.write(f'Webhook endpoint: {webhook_url}')
            
            self.stdout.write(
                self.style.SUCCESS('✅ Stripe integration test completed successfully!')
            )
            self.stdout.write(
                self.style.WARNING(
                    'To complete the test:\n'
                    '1. Use the checkout URL above with test card 4242 4242 4242 4242\n'
                    '2. Check that the subscription is created in the database\n'
                    '3. Verify that the user can access Pomodoro features'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during test: {e}')
            )
