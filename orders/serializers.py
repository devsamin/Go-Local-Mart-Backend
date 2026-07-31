from rest_framework import serializers

from products.serializers import ProductSerializer
from reviews.models import Review
from .models import Order, OrderItem
from .services import available_fulfillment_statuses


class SellerOrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    buyer_name = serializers.CharField(source="order.user.username", read_only=True)
    ordered_at = serializers.DateTimeField(source="order.created_at", read_only=True)
    available_statuses = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = (
            "id", "order", "product", "product_name", "quantity", "price", "status",
            "buyer_name", "ordered_at", "available_statuses",
        )
        read_only_fields = (
            "id", "order", "product", "product_name", "quantity", "price",
            "buyer_name", "ordered_at", "available_statuses",
        )

    def get_available_statuses(self, obj):
        return available_fulfillment_statuses(obj.status)


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    review = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_name", "quantity", "price", "seller", "status", "review")

    def get_review(self, obj):
        try:
            review = obj.review
        except Review.DoesNotExist:
            return None
        return {"id": review.id, "rating": review.rating, "comment": review.comment}


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "user", "total_price", "status", "payment_method", "is_paid",
            "created_at", "updated_at", "items",
        )
        read_only_fields = fields
