from decimal import Decimal
from urllib.parse import urljoin

import stripe
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Order
from orders.services import cancel_and_release_order


stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_stripe_checkout(request):
    try:
        order_id = int(request.data.get("order_id"))
    except (TypeError, ValueError):
        raise ValidationError({"order_id": "A valid order ID is required."})

    try:
        order = Order.objects.prefetch_related("items__product").get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

    if order.is_paid:
        raise ValidationError({"order_id": "This order is already paid."})
    if order.status == "cancelled" or not order.inventory_reserved:
        raise ValidationError({"order_id": "This checkout has expired. Please place the order again."})
    if not settings.STRIPE_SECRET_KEY:
        return Response({"error": "Payments are not configured."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    line_items = []
    items_total = Decimal("0.00")
    for item in order.items.all():
        product_data = {"name": item.product_name}
        if item.product and item.product.image:
            image_url = item.product.image.url
            if image_url.startswith("/"):
                image_url = urljoin(f"{settings.BACKEND_BASE_URL}/", image_url.lstrip("/"))
            if image_url.startswith("https://"):
                product_data["images"] = [image_url]
        line_items.append(
            {
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY,
                    "product_data": product_data,
                    "unit_amount": int(item.price * 100),
                },
                "quantity": item.quantity,
            }
        )
        items_total += item.price * item.quantity

    service_fee = order.total_price - items_total
    if service_fee > 0:
        line_items.append(
            {
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY,
                    "product_data": {"name": "Delivery"},
                    "unit_amount": int(service_fee * 100),
                },
                "quantity": 1,
            }
        )

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=line_items,
            success_url=f"{settings.FRONTEND_URL}/payment-success?order_id={order.id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/payment-failed?order_id={order.id}",
            metadata={"order_id": str(order.id), "user_id": str(request.user.id)},
            client_reference_id=str(order.id),
        )
    except stripe.StripeError:
        cancel_and_release_order(order, restore_cart=True)
        return Response(
            {"error": "The payment provider could not start checkout. Your cart was restored."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    order.stripe_session_id = session.id
    order.save(update_fields=["stripe_session_id", "updated_at"])
    return Response({"checkout_url": session.url, "order_id": order.id})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_status(request):
    try:
        order_id = int(request.query_params.get("order_id"))
    except (TypeError, ValueError):
        raise ValidationError({"order_id": "A valid order ID is required."})
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(
        {"order_id": order.id, "paid": order.is_paid, "status": order.status},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_stripe_checkout(request):
    """Expire an open Stripe session before releasing its reserved inventory."""
    try:
        order_id = int(request.data.get("order_id"))
    except (TypeError, ValueError):
        raise ValidationError({"order_id": "A valid order ID is required."})

    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

    if order.is_paid:
        raise ValidationError({"order_id": "A paid order cannot be cancelled here."})
    if order.status == "cancelled" or not order.inventory_reserved:
        return Response({"message": "Checkout was already cancelled."})

    if order.stripe_session_id:
        if not settings.STRIPE_SECRET_KEY:
            return Response(
                {"error": "Payments are not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        try:
            session = stripe.checkout.Session.retrieve(order.stripe_session_id)
            if session.payment_status == "paid":
                raise ValidationError({"order_id": "This payment has already completed."})
            if session.status == "open":
                stripe.checkout.Session.expire(order.stripe_session_id)
            elif session.status != "expired":
                return Response(
                    {"error": "The checkout could not be safely cancelled."},
                    status=status.HTTP_409_CONFLICT,
                )
        except stripe.StripeError:
            return Response(
                {"error": "Stripe could not cancel the checkout. Inventory was not released."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

    order = cancel_and_release_order(order, restore_cart=True)
    return Response({"message": "Checkout cancelled and cart restored.", "status": order.status})
