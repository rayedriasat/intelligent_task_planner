from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SubscriptionPlan(models.Model):
    """Represents different subscription plans available."""
    PLAN_TYPES = [
        ('pomodoro', 'Pomodoro'),
        ('ai_chat', 'AI Chat'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True)
    features = models.JSONField(default=list)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ${self.price}/month"


class Subscription(models.Model):
    """Represents a user's subscription to a specific plan."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('trialing', 'Trialing'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    stripe_subscription_id = models.CharField(max_length=100, unique=True)
    stripe_customer_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='incomplete')
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'plan']
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        """Check if subscription is currently active."""
        return self.status in ['active', 'trialing'] and self.current_period_end > timezone.now()


class Customer(models.Model):
    """Represents a Stripe customer."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stripe_customer')
    stripe_customer_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.stripe_customer_id}"


class PaymentIntent(models.Model):
    """Track payment intents for subscriptions."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stripe_payment_intent_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='usd')
    status = models.CharField(max_length=50)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.stripe_payment_intent_id} - ${self.amount}"
