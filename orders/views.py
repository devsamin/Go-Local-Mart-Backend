from decimal import Decimal

from django.db import transaction
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from cart.models import Cart, CartItem
from products.models import Product
from reviews.models import Review
from .models import Order, OrderItem
from .serializers import OrderSerializer, SellerOrderItemSerializer
from .services import cancel_and_release_order


DELIVERY_FEE = Decimal("60.00")


class SellerOrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = SellerOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ("get", "patch", "head", "options")

    def get_queryset(self):
        if self.request.user.role != "seller":
            raise PermissionDenied("A seller account is required.")
        return OrderItem.objects.filter(seller=self.request.user).select_related(
            "order__user", "product__seller"
        ).prefetch_related("product__categories")

    def partial_update(self, request, *args, **kwargs):
        item = self.get_object()
        next_status = request.data.get("status")
        transitions = {
            "pending": {"processing"},
            "processing": {"shipped"},
            "shipped": {"delivered"},
            "delivered": set(),
            "cancelled": set(),
        }
        if not item.order.is_paid:
            raise ValidationError({"status": "Payment has not been confirmed."})
        if next_status not in transitions[item.status]:
            raise ValidationError({"status": f"Cannot change {item.status} to {next_status}."})

        item.status = next_status
        item.save(update_fields=["status"])
        statuses = set(item.order.items.values_list("status", flat=True))
        if statuses == {"delivered"}:
            order_status = "delivered"
        elif "shipped" in statuses or "delivered" in statuses:
            order_status = "shipped"
        elif "processing" in statuses:
            order_status = "processing"
        elif statuses == {"cancelled"}:
            order_status = "cancelled"
        else:
            order_status = "pending"
        item.order.status = order_status
        item.order.save(update_fields=["status", "updated_at"])
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
