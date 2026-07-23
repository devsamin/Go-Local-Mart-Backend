import stripe
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from orders.services import cancel_and_release_order


stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse(status=503)

    try:
        event = stripe.Webhook.construct_event(
            payload=request.body,
            sig_header=request.headers.get("Stripe-Signature", ""),
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse(status=400)

    session = event["data"]["object"]
    order_id = session.get("metadata", {}).get("order_id")
    if not order_id:
        return HttpResponse(status=200)

    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return HttpResponse(status=200)

    if event["type"] in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=order.pk)
            if not order.is_paid and session.get("payment_status") == "paid":
                order.is_paid = True
                order.status = "pending"
                order.transaction_id = session.get("payment_intent") or ""
                order.stripe_session_id = session.get("id") or order.stripe_session_id
                order.save(
                    update_fields=[
                        "is_paid", "status", "transaction_id", "stripe_session_id", "updated_at"
                    ]
                )
    elif event["type"] in {"checkout.session.expired", "checkout.session.async_payment_failed"}:
        cancel_and_release_order(order, restore_cart=True)

    return HttpResponse(status=200)
