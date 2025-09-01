import json
import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from .models import SubscriptionPlan, Subscription
from .services import StripeService, user_has_subscription
import logging

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscribeView(LoginRequiredMixin, TemplateView):
    """Subscription plans page."""
    template_name = 'billing/subscribe.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = SubscriptionPlan.objects.filter(active=True)
        
        # Get user's current subscriptions
        user_subscriptions = {}
        if self.request.user.is_authenticated:
            for sub in self.request.user.subscriptions.filter(status__in=['active', 'trialing']):
                if sub.is_active:
                    user_subscriptions[sub.plan.plan_type] = sub
        
        context['user_subscriptions'] = user_subscriptions
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        
        return context


@login_required
@require_POST
def create_checkout_session(request):
    """Create a Stripe checkout session."""
    try:
        plan_id = request.POST.get('plan_id')
        plan = get_object_or_404(SubscriptionPlan, id=plan_id, active=True)
        
        # Check if user already has this subscription
        if user_has_subscription(request.user, plan.plan_type):
            return JsonResponse({
                'success': False,
                'error': f'You already have an active {plan.name} subscription.'
            })
        
        # Create checkout session
        checkout_session = StripeService.create_checkout_session(
            request.user, plan, request
        )
        
        return JsonResponse({
            'success': True,
            'checkout_url': checkout_session.url
        })
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to create checkout session. Please try again.'
        })


class SuccessView(LoginRequiredMixin, TemplateView):
    """Subscription success page."""
    template_name = 'billing/success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = self.request.GET.get('session_id')
        
        if session_id:
            try:
                # Retrieve the checkout session from Stripe
                session = stripe.checkout.Session.retrieve(session_id)
                
                if session.payment_status == 'paid':
                    user_id = session.metadata.get('user_id')
                    plan_id = session.metadata.get('plan_id')
                    
                    if user_id and plan_id:
                        user = User.objects.get(id=user_id)
                        plan = SubscriptionPlan.objects.get(id=plan_id)
                        
                        # Check if subscription already exists (any status)
                        existing_sub = Subscription.objects.filter(
                            user=user,
                            plan=plan
                        ).first()
                        
                        if existing_sub:
                            # Update existing subscription to active
                            existing_sub.stripe_subscription_id = session.subscription
                            existing_sub.stripe_customer_id = session.customer
                            existing_sub.status = 'active'
                            
                            # Update period if needed
                            from django.utils import timezone
                            if not existing_sub.current_period_start or existing_sub.status in ['canceled', 'incomplete']:
                                now = timezone.now()
                                existing_sub.current_period_start = now
                                existing_sub.current_period_end = now + timezone.timedelta(days=30)
                            
                            existing_sub.save()
                            context['success'] = True
                            context['subscription'] = existing_sub
                            logger.info(f"Updated existing subscription for user {user.email}")
                        else:
                            # Create new subscription record
                            from django.utils import timezone
                            now = timezone.now()
                            
                            subscription = Subscription.objects.create(
                                user=user,
                                plan=plan,
                                stripe_subscription_id=session.subscription,
                                stripe_customer_id=session.customer,
                                status='active',
                                current_period_start=now,
                                current_period_end=now + timezone.timedelta(days=30)
                            )
                            context['success'] = True
                            context['subscription'] = subscription
                            logger.info(f"Created new subscription for user {user.email}")
                    else:
                        context['error'] = 'Missing user or plan information'
                else:
                    context['error'] = 'Payment not completed'
                    
            except Exception as e:
                logger.error(f"Error handling success: {e}")
                context['error'] = f'There was an issue processing your subscription: {str(e)}'
        else:
            context['error'] = 'No session ID provided'
        
        return context


class ManageSubscriptionsView(LoginRequiredMixin, TemplateView):
    """Manage user subscriptions."""
    template_name = 'billing/manage.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscriptions'] = self.request.user.subscriptions.all().order_by('-created_at')
        return context


@login_required
@require_POST
def cancel_subscription(request):
    """Cancel a user's subscription."""
    try:
        subscription_id = request.POST.get('subscription_id')
        subscription = get_object_or_404(
            Subscription, 
            id=subscription_id, 
            user=request.user
        )
        
        # Cancel the subscription in Stripe
        StripeService.cancel_subscription(subscription)
        
        messages.success(request, f'Your {subscription.plan.name} subscription has been cancelled.')
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to cancel subscription. Please try again.'
        })


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload in webhook")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in webhook")
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        try:
            StripeService.handle_successful_payment(session['id'])
        except Exception as e:
            logger.error(f"Error handling checkout.session.completed: {e}")
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        try:
            StripeService.sync_subscription_status(subscription['id'])
        except Exception as e:
            logger.error(f"Error handling subscription.updated: {e}")
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        try:
            sub_obj = Subscription.objects.get(
                stripe_subscription_id=subscription['id']
            )
            sub_obj.status = 'canceled'
            sub_obj.save()
            logger.info(f"Subscription {subscription['id']} marked as cancelled")
        except Subscription.DoesNotExist:
            logger.warning(f"Subscription {subscription['id']} not found in database")
        except Exception as e:
            logger.error(f"Error handling subscription.deleted: {e}")
    
    elif event['type'] == 'invoice.payment_failed':
        # Handle failed payments
        invoice = event['data']['object']
        subscription_id = invoice['subscription']
        try:
            sub_obj = Subscription.objects.get(
                stripe_subscription_id=subscription_id
            )
            sub_obj.status = 'past_due'
            sub_obj.save()
            logger.info(f"Subscription {subscription_id} marked as past_due")
        except Subscription.DoesNotExist:
            logger.warning(f"Subscription {subscription_id} not found for failed payment")
        except Exception as e:
            logger.error(f"Error handling invoice.payment_failed: {e}")
    
    else:
        logger.info(f"Unhandled event type: {event['type']}")
    
    return HttpResponse(status=200)
