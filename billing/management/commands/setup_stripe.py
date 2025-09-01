import stripe
from django.core.management.base import BaseCommand
from django.conf import settings
from billing.models import SubscriptionPlan

class Command(BaseCommand):
    help = 'Set up Stripe products and subscription plans'

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        self.stdout.write('Setting up Stripe products and plans...')
        
        # Create Pomodoro Plan
        try:
            # Create product
            pomodoro_product = stripe.Product.create(
                name='Pomodoro Timer Access',
                description='Access to the Pomodoro timer feature for focused work sessions'
            )
            
            # Create price
            pomodoro_price = stripe.Price.create(
                product=pomodoro_product.id,
                unit_amount=500,  # $5.00 in cents
                currency='usd',
                recurring={'interval': 'month'}
            )
            
            # Create or update in database
            pomodoro_plan, created = SubscriptionPlan.objects.update_or_create(
                plan_type='pomodoro',
                defaults={
                    'name': 'Pomodoro Timer',
                    'price': 5.00,
                    'stripe_price_id': pomodoro_price.id,
                    'description': 'Unlock the Pomodoro timer for focused work sessions',
                    'features': [
                        'Pomodoro timer with customizable intervals',
                        'Focus session tracking',
                        'Break reminders',
                        'Productivity statistics',
                        'Task-linked focus sessions'
                    ],
                    'active': True
                }
            )
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{action} Pomodoro plan: {pomodoro_price.id}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating Pomodoro plan: {e}')
            )
        
        # Create AI Chat Plan
        try:
            # Create product
            ai_product = stripe.Product.create(
                name='AI Schedule Assistant',
                description='Access to AI-powered scheduling and productivity assistant'
            )
            
            # Create price
            ai_price = stripe.Price.create(
                product=ai_product.id,
                unit_amount=1000,  # $10.00 in cents
                currency='usd',
                recurring={'interval': 'month'}
            )
            
            # Create or update in database
            ai_plan, created = SubscriptionPlan.objects.update_or_create(
                plan_type='ai_chat',
                defaults={
                    'name': 'AI Schedule Assistant',
                    'price': 10.00,
                    'stripe_price_id': ai_price.id,
                    'description': 'Get personalized scheduling advice from AI',
                    'features': [
                        'AI chat assistant for scheduling',
                        'Personalized productivity recommendations',
                        'Intelligent schedule optimization',
                        'Context-aware task suggestions',
                        'Schedule analysis and insights'
                    ],
                    'active': True
                }
            )
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{action} AI Chat plan: {ai_price.id}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating AI Chat plan: {e}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Stripe setup complete!')
        )
