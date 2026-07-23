from rest_framework import serializers

from users.serializers import ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE
from localmart_backend.media import optimized_image_url
from .models import SpecialOffer


class SpecialOfferSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.username", read_only=True)

    class Meta:
        model = SpecialOffer
        fields = (
            "id", "seller", "seller_name", "title", "subtitle", "image", "badge",
            "badgeColor", "is_active", "created_at",
        )
        read_only_fields = ("id", "seller", "created_at")

    def validate_image(self, image):
        if image.size > MAX_IMAGE_SIZE:
            raise serializers.ValidationError("Images must be 5 MB or smaller.")
        content_type = getattr(image, "content_type", "")
        if content_type and content_type not in ALLOWED_IMAGE_TYPES:
            raise serializers.ValidationError("Use a JPEG, PNG, or WebP image.")
        return image

    def validate_badgeColor(self, value):
        allowed = {"bg-emerald-600", "bg-blue-600", "bg-amber-600", "bg-rose-600", "bg-violet-600"}
        if value not in allowed:
            raise serializers.ValidationError("Choose a supported badge color.")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["image"] = optimized_image_url(
            instance.image, request=self.context.get("request"), width=1600
        )
        return data
