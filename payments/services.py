from django.db import transaction

from orders.models import Order


class PaymentConfirmationError(Exception):
    """Raised when a Stripe session cannot safely confirm an order."""


@transaction.atomic
def confirm_order_payment(order_id, session):
    """Verify a Stripe Checkout Session and make its order seller-visible."""
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.is_paid:
        return order

    session_id = str(session.get("id") or "")
    metadata = session.get("metadata") or {}
    payment_status = session.get("payment_status")
    amount_total = session.get("amount_total")
    currency = str(session.get("currency") or "").lower()

    if payment_status != "paid":
        raise PaymentConfirmationError("Stripe has not confirmed this payment.")
    if not session_id or (order.stripe_session_id and session_id != order.stripe_session_id):
        raise PaymentConfirmationError("The Stripe session does not belong to this order.")
    if str(metadata.get("order_id") or "") != str(order.id):
        raise PaymentConfirmationError("The Stripe session has invalid order metadata.")
    if str(metadata.get("user_id") or "") != str(order.user_id):
        raise PaymentConfirmationError("The Stripe session has invalid buyer metadata.")
    if amount_total is not None and int(amount_total) != int(order.total_price * 100):
        raise PaymentConfirmationError("The paid amount does not match the order total.")
    if currency and currency != order_currency():
        raise PaymentConfirmationError("The payment currency does not match the order.")
    if order.status == "cancelled" or not order.inventory_reserved:
        raise PaymentConfirmationError("This order no longer has reserved inventory.")

    order.is_paid = True
    order.inventory_reserved = False
    order.status = "pending"
    order.transaction_id = str(session.get("payment_intent") or "")
    order.stripe_session_id = session_id
    order.save(
        update_fields=[
            "is_paid",
            "inventory_reserved",
            "status",
            "transaction_id",
            "stripe_session_id",
            "updated_at",
        ]
    )
    return order


def order_currency():
    # Imported lazily so tests can override the setting.
    from django.conf import settings

    return settings.STRIPE_CURRENCY.lower()
