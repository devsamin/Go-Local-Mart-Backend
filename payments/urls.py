from django.urls import path

from .views import (
    cancel_stripe_checkout,
    confirm_stripe_checkout,
    create_stripe_checkout,
    payment_status,
)
from .webhooks import stripe_webhook


urlpatterns = [
    path("stripe/checkout/", create_stripe_checkout, name="stripe-checkout"),
    path("stripe/confirm/", confirm_stripe_checkout, name="stripe-confirm"),
    path("stripe/cancel/", cancel_stripe_checkout, name="stripe-cancel"),
    path("stripe/webhook/", stripe_webhook, name="stripe-webhook"),
    path("status/", payment_status, name="payment-status"),
]
