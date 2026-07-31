from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from cart.models import Cart, CartItem
from products.models import Product
from reviews.models import Review
from .models import Order, OrderItem
from .serializers import OrderSerializer, SellerOrderItemSerializer
from .services import (
    aggregate_order_status,
    available_fulfillment_statuses,
    cancel_and_release_order,
    cancel_paid_order_item,
)


DELIVERY_FEE = Decimal("60.00")


class SellerOrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = SellerOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ("get", "patch", "head", "options")

    def get_queryset(self):
        if self.request.user.role != "seller":
            raise PermissionDenied("A seller account is required.")
        return OrderItem.objects.filter(
            seller=self.request.user,
            order__is_paid=True,
        ).select_related(
            "order__user", "product__seller"
        ).prefetch_related("product__categories").order_by("-order__created_at", "-id")

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        item = get_object_or_404(
            self.get_queryset().select_for_update(),
            pk=kwargs["pk"],
        )
        order = Order.objects.select_for_update().get(pk=item.order_id)
        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        next_status = serializer.validated_data.get("status")
        allowed_statuses = {
            option["value"] for option in available_fulfillment_statuses(item.status)
        }
        if next_status not in allowed_statuses:
            raise ValidationError({"status": f"Cannot change {item.status} to {next_status}."})

        if next_status == "cancelled":
            item = cancel_paid_order_item(item)
        else:
            item.status = next_status
            item.save(update_fields=["status"])
            order.status = aggregate_order_status(
                order.items.values_list("status", flat=True)
            )
            order.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(item).data)


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "items__product__seller", "items__product__categories", "items__review"
        )

    @action(detail=True, methods=("post",))
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.is_paid:
            raise ValidationError({"order": "Paid orders must be cancelled through support."})
        if order.stripe_session_id:
            raise ValidationError(
                {"order": "Use the payment cancellation endpoint for an active Stripe checkout."}
            )
        order = cancel_and_release_order(order, restore_cart=True)
        return Response({"message": "Checkout cancelled and cart restored.", "status": order.status})

    @action(detail=False, methods=("post",), url_path="checkout")
    def checkout(self, request):
        if request.user.role != "buyer":
            raise PermissionDenied("A buyer account is required.")
        with transaction.atomic():
            try:
                cart = Cart.objects.select_for_update().get(user=request.user)
            except Cart.DoesNotExist:
                raise ValidationError({"cart": "Your cart is empty."})

            cart_items = list(CartItem.objects.filter(cart=cart).select_related("product__seller"))
            if not cart_items:
                raise ValidationError({"cart": "Your cart is empty."})

            product_ids = [item.product_id for item in cart_items]
            products = {
                product.id: product
                for product in Product.objects.select_for_update().filter(id__in=product_ids)
            }
            unavailable = [
                item.product.name for item in cart_items
                if item.product_id not in products or products[item.product_id].stock < item.quantity
            ]
            if unavailable:
                raise ValidationError({"cart": f"Insufficient stock for: {', '.join(unavailable)}."})

            subtotal = sum(
                (products[item.product_id].discounted_price * item.quantity for item in cart_items),
                start=Decimal("0.00"),
            )
            order = Order.objects.create(
                user=request.user,
                total_price=subtotal + DELIVERY_FEE,
                payment_method="stripe",
                inventory_reserved=True,
            )
            order_items = []
            for item in cart_items:
                product = products[item.product_id]
                product.stock -= item.quantity
                product.save(update_fields=["stock"])
                order_items.append(
                    OrderItem(
                        order=order,
                        product=product,
                        seller=product.seller,
                        product_name=product.name,
                        quantity=item.quantity,
                        price=product.discounted_price,
                    )
                )
            OrderItem.objects.bulk_create(order_items)
            CartItem.objects.filter(cart=cart).delete()

        return Response(
            {"order_id": order.id, "total_price": order.total_price}, status=status.HTTP_201_CREATED
        )
