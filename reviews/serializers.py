from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id", "product", "product_name", "user", "username", "order_item",
            "rating", "comment", "created_at", "updated_at",
        )
        read_only_fields = ("id", "product", "user", "order_item", "created_at", "updated_at")
