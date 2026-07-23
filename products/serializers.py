from rest_framework import serializers

from category.models import Category
from category.serializers import CategorySerializer
from users.serializers import ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE
from localmart_backend.media import optimized_image_url
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.username", read_only=True)
    seller_location = serializers.CharField(source="seller.location", read_only=True)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True, default=0)
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Category.objects.all(), source="categories", required=False
    )
    categories = CategorySerializer(many=True, read_only=True)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "seller", "seller_name", "seller_location", "name", "description",
            "price", "discount", "discounted_price", "stock", "is_available", "image",
            "image2", "image3", "category_ids", "categories", "average_rating", "created_at",
        ]
        read_only_fields = ["id", "seller", "created_at"]

    def validate(self, attrs):
        price = attrs.get("price", getattr(self.instance, "price", None))
        discount = attrs.get("discount", getattr(self.instance, "discount", 0))
        if price is not None and discount == 100:
            raise serializers.ValidationError({"discount": "A product cannot be discounted to zero."})
        for field in ("image", "image2", "image3"):
            image = attrs.get(field)
            if not image:
                continue
            if image.size > MAX_IMAGE_SIZE:
                raise serializers.ValidationError({field: "Images must be 5 MB or smaller."})
            content_type = getattr(image, "content_type", "")
            if content_type and content_type not in ALLOWED_IMAGE_TYPES:
                raise serializers.ValidationError({field: "Use a JPEG, PNG, or WebP image."})
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        for field in ("image", "image2", "image3"):
            data[field] = optimized_image_url(getattr(instance, field), request=request)
        return data
