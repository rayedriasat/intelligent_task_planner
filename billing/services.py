import stripe
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime
from .models import Customer, Subscription, SubscriptionPlan
import logging

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service class for handling Stripe operations."""
    
    @staticmethod
    def get_or_create_customer(user):
        """Get or create a Stripe customer for a Django user."""
        try:
            customer_obj = Customer.objects.get(user=user)
            return customer_obj.stripe_customer_id
        except Customer.DoesNotExist:
            # Create new Stripe customer
            stripe_customer = stripe.Customer.create(
                email=user.email,
                name=user.get_full_name() or user.username,
                metadata={'user_id': user.id}
            )
            
            # Save to database
            customer_obj = Customer.objects.create(
                user=user,
                stripe_customer_id=stripe_customer.id
            )
            
            return stripe_customer.id
    
    @staticmethod
    def create_checkout_session(user, plan, request):
        """Create a Stripe checkout session for subscription."""
        try:
            customer_id = StripeService.get_or_create_customer(user)
            
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=request.build_absolute_uri(
                    reverse('billing:success')
                ) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(
                    reverse('billing:subscribe')
                ),
                metadata={
                    'user_id': user.id,
                    'plan_id': plan.id,
                }
            )
            
            return checkout_session
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            raise
    
    @staticmethod
    def handle_successful_payment(session_id):
        """Handle successful payment from Stripe webhook."""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                user_id = session.metadata.get('user_id')
                plan_id = session.metadata.get('plan_id')
                
                if user_id and plan_id:
                    user = User.objects.get(id=user_id)
                    plan = SubscriptionPlan.objects.get(id=plan_id)
                    
                    # Get the subscription from Stripe
                    subscription = stripe.Subscription.retrieve(session.subscription)
                    
                    # Create or update subscription in database
                    sub_obj, created = Subscription.objects.update_or_create(
                        user=user,
                        plan=plan,
                        defaults={
                            'stripe_subscription_id': subscription.id,
                            'stripe_customer_id': subscription.customer,
                            'status': subscription.status,
                            'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
                            'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                        }
                    )
                    
                    logger.info(f"Subscription {'created' if created else 'updated'} for user {user.email}")
                    return sub_obj
                    
        except Exception as e:
            logger.error(f"Error handling successful payment: {e}")
            raise
    
    @staticmethod
    def cancel_subscription(subscription):
        """Cancel a subscription."""
        try:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
            subscription.status = 'canceled'
            subscription.save()
            logger.info(f"Subscription cancelled for user {subscription.user.email}")
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            raise
    
    @staticmethod
    def sync_subscription_status(stripe_subscription_id):
        """Sync subscription status with Stripe."""
        try:
            stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
            
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
            
            subscription.status = stripe_sub.status
            subscription.current_period_start = datetime.fromtimestamp(stripe_sub.current_period_start)
            subscription.current_period_end = datetime.fromtimestamp(stripe_sub.current_period_end)
            subscription.save()
            
            return subscription
            
        except Exception as e:
            logger.error(f"Error syncing subscription status: {e}")
            raise


def user_has_subscription(user, plan_type):
    """Check if a user has an active subscription for a specific plan type."""
    if not user.is_authenticated:
        return False
    
    try:
        subscription = Subscription.objects.get(
            user=user,
            plan__plan_type=plan_type,
            status__in=['active', 'trialing']
        )
        return subscription.is_active
    except Subscription.DoesNotExist:
        return False


def user_has_pomodoro_access(user):
    """Check if user has access to Pomodoro features."""
    return user_has_subscription(user, 'pomodoro')


def user_has_ai_chat_access(user):
    """Check if user has access to AI Chat features."""
    return user_has_subscription(user, 'ai_chat')
