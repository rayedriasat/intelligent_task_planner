from django.contrib import admin
from .models import SubscriptionPlan, Subscription, Customer, PaymentIntent


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'active', 'created_at']
    list_filter = ['plan_type', 'active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['stripe_price_id', 'created_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'current_period_start', 'current_period_end', 'created_at']
    list_filter = ['status', 'plan__plan_type', 'created_at']
    search_fields = ['user__email', 'user__username', 'stripe_subscription_id']
    readonly_fields = ['stripe_subscription_id', 'stripe_customer_id', 'created_at', 'updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing subscription
            return self.readonly_fields + ['user', 'plan']
        return self.readonly_fields


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'stripe_customer_id', 'created_at']
    search_fields = ['user__email', 'user__username', 'stripe_customer_id']
    readonly_fields = ['stripe_customer_id', 'created_at', 'updated_at']


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'status', 'plan', 'created_at']
    list_filter = ['status', 'currency', 'plan__plan_type', 'created_at']
    search_fields = ['user__email', 'stripe_payment_intent_id']
    readonly_fields = ['stripe_payment_intent_id', 'created_at']
