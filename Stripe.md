# Billing System Documentation

## Overview

This billing system integrates Stripe subscriptions with the Django Task Planner application. It provides two subscription tiers:

- **Pomodoro Subscription** ($5/month) - Access to Pomodoro timer features
- **AI Chat Subscription** ($10/month) - Access to AI scheduling assistant

## Features

### ✅ Implemented Features

1. **Stripe Integration**
   - Secure payment processing with Stripe Checkout
   - Subscription management with webhooks
   - Test mode configuration for development

2. **Subscription Plans**
   - Two distinct subscription tiers
   - Database models for plans, subscriptions, and customers
   - Admin interface for subscription management

3. **Access Control**
   - Decorators for function-based views
   - Mixins for class-based views
   - Automatic redirects to subscription page when access denied

4. **User Interface**
   - Premium subscription page with plan comparison
   - Subscription management dashboard
   - Success/error pages for checkout flow
   - Visual indicators in navigation (🔒 for locked features)

5. **Webhook Integration**
   - Handles subscription events from Stripe
   - Automatic status synchronization
   - Payment failure handling

## Setup Instructions

### 1. Environment Configuration

Add these variables to your `.env` file:
```env
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 2. Database Migration

```bash
uv run python manage.py makemigrations billing
uv run python manage.py migrate
```

### 3. Create Stripe Products

```bash
uv run python manage.py setup_stripe
```

### 4. Test Integration

```bash
uv run python manage.py test_stripe --email test@example.com
```

## URL Structure

- `/billing/subscribe/` - Subscription plans page
- `/billing/success/` - Post-payment success page
- `/billing/manage/` - User subscription management
- `/billing/webhook/` - Stripe webhook endpoint (for Stripe)

## Usage

### For Users

1. **Subscribing**: Click "PREMIUM" in navigation → Choose plan → Complete Stripe checkout
2. **Managing**: Visit "My Subscriptions" to view/cancel subscriptions
3. **Accessing Features**: Premium features are automatically unlocked after subscription

### For Developers

#### Access Control

```python
# Function-based views
from billing.decorators import pomodoro_required, ai_chat_required

@pomodoro_required
def my_pomodoro_view(request):
    # Only accessible with Pomodoro subscription
    pass

@ai_chat_required
def my_ai_view(request):
    # Only accessible with AI Chat subscription
    pass

# Class-based views
from billing.decorators import PomodoroRequiredMixin, AIChatRequiredMixin

class MyPomodoroView(PomodoroRequiredMixin, TemplateView):
    # Only accessible with Pomodoro subscription
    pass
```

#### Check Subscription Status

```python
from billing.services import user_has_pomodoro_access, user_has_ai_chat_access

if user_has_pomodoro_access(request.user):
    # User has Pomodoro subscription
    pass

if user_has_ai_chat_access(request.user):
    # User has AI Chat subscription
    pass
```

## Testing

### Test Cards (Stripe Test Mode)

- **Success**: 4242 4242 4242 4242
- **Decline**: 4000 0000 0000 0002
- **3D Secure**: 4000 0000 0000 3220

### Test Scenarios

1. **Subscribe to Pomodoro**
   - Visit `/billing/subscribe/`
   - Click "Subscribe to Pomodoro Timer"
   - Use test card 4242 4242 4242 4242
   - Verify access to `/pomodoro/`

2. **Subscribe to AI Chat**
   - Visit `/billing/subscribe/`
   - Click "Subscribe to AI Schedule Assistant"
   - Use test card 4242 4242 4242 4242
   - Verify access to `/ai-chat/`

3. **Access Control**
   - Without subscription, visit `/pomodoro/` or `/ai-chat/`
   - Should redirect to subscription page with appropriate message

## Webhook Configuration

For production, configure webhook endpoint in Stripe Dashboard:
- URL: `https://yourdomain.com/billing/webhook/`
- Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`

## Security Notes

- All payment processing happens on Stripe's secure servers
- No card details are stored in your database
- Webhook signatures are verified for security
- Test keys are used for development (prefix `pk_test_` and `sk_test_`)

## Database Models

- `SubscriptionPlan` - Available subscription plans
- `Subscription` - User subscriptions linked to Stripe
- `Customer` - Stripe customer records
- `PaymentIntent` - Payment tracking (optional)

## Admin Interface

Access at `/admin/` to:
- View all subscriptions
- Manage subscription plans
- Monitor payment intents
- View customer records

## Troubleshooting

### Common Issues

1. **Subscription not activated after payment**
   - Check webhook endpoint is configured
   - Verify webhook secret is correct
   - Check Django logs for webhook errors

2. **Access still denied after subscription**
   - Verify subscription status in admin interface
   - Check if subscription end date is in the future
   - Ensure subscription status is "active" or "trialing"

3. **Checkout session creation fails**
   - Verify Stripe keys are correct
   - Check if plans exist in Stripe dashboard
   - Ensure `setup_stripe` command was run

### Logs

Check Django logs for detailed error information:
```python
import logging
logger = logging.getLogger(__name__)
```

## Future Enhancements

- [ ] Prorated upgrades/downgrades
- [ ] Usage-based billing
- [ ] Team/organization subscriptions
- [ ] Discount codes and promotions
- [ ] Invoice generation
- [ ] Email notifications for billing events
