from django.db import transaction

from cart.models import Cart, CartItem
from products.models import Product


FULFILLMENT_SEQUENCE = ("pending", "processing", "shipped", "delivered")
FULFILLMENT_LABELS = {
    "processing": "Processing",
    "shipped": "Shipping",
    "delivered": "Delivered",
}


def available_fulfillment_statuses(current_status):
    """Return the forward-only statuses a seller may choose."""
    try:
        current_index = FULFILLMENT_SEQUENCE.index(current_status)
    except ValueError:
        return []
    return [
        {"value": value, "label": FULFILLMENT_LABELS[value]}
        for value in FULFILLMENT_SEQUENCE[current_index + 1:]
    ]


def aggregate_order_status(item_statuses):
    """Derive the buyer-visible order status from all seller-owned items."""
    statuses = set(item_statuses)
    if not statuses:
        return "pending"
    if statuses == {"cancelled"}:
        return "cancelled"
    active_statuses = statuses - {"cancelled"}
    if active_statuses and active_statuses == {"delivered"}:
        return "delivered"
    if active_statuses and active_statuses <= {"shipped", "delivered"}:
        return "shipped"
    if active_statuses & {"processing", "shipped", "delivered"}:
        return "processing"
    return "pending"


@transaction.atomic
def cancel_and_release_order(order, restore_cart=False):
    """Release reserved inventory once; safe to call for duplicate Stripe events."""
    order = type(order).objects.select_for_update().get(pk=order.pk)
    if order.is_paid or not order.inventory_reserved:
        return order

    items = list(order.items.select_related("product"))
    product_ids = [item.product_id for item in items if item.product_id]
    products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)}
    for item in items:
        product = products.get(item.product_id)
        if product:
            product.stock += item.quantity
            product.save(update_fields=["stock"])

    if restore_cart:
        cart, _ = Cart.objects.get_or_create(user=order.user)
        for item in items:
            if not item.product_id:
                continue
            cart_item = CartItem.objects.select_for_update().filter(
                cart=cart, product_id=item.product_id
            ).first()
            if cart_item:
                cart_item.quantity += item.quantity
                cart_item.save(update_fields=["quantity"])
            else:
                CartItem.objects.create(
                    cart=cart, product_id=item.product_id, quantity=item.quantity
                )

    order.inventory_reserved = False
    order.status = "cancelled"
    order.save(update_fields=["inventory_reserved", "status", "updated_at"])
    order.items.exclude(status="delivered").update(status="cancelled")
    return order
