from django.urls import path

from .views import create_stripe_checkout, payment_status
from .webhooks import stripe_webhook


urlpatterns = [
    path("stripe/checkout/", create_stripe_checkout, name="stripe-checkout"),
    path("stripe/webhook/", stripe_webhook, name="stripe-webhook"),
    path("status/", payment_status, name="payment-status"),
]
