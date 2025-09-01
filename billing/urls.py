from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.SuccessView.as_view(), name='success'),
    path('manage/', views.ManageSubscriptionsView.as_view(), name='manage'),
    path('cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]
