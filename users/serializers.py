import re

from django.contrib.auth import authenticate, password_validation
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User
from localmart_backend.media import optimized_image_url


MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def validate_profile_image(image):
    if image.size > MAX_IMAGE_SIZE:
        raise serializers.ValidationError("Profile images must be 5 MB or smaller.")
    content_type = getattr(image, "content_type", "")
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise serializers.ValidationError("Use a JPEG, PNG, or WebP image.")
    return image


class ProfileImageField(serializers.ImageField):
    """Accept profile uploads and retain the optimized URL representation."""

    def to_representation(self, value):
        return optimized_image_url(
            value,
            request=self.context.get("request"),
            width=512,
        )


class RegisterSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False, validators=[validate_profile_image])
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "password", "role", "location", "phone",
            "address", "photo", "businessName", "nidNumber", "bankAccount",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_role(self, value):
        if value not in {"buyer", "seller"}:
            raise serializers.ValidationError("Choose either buyer or seller.")
        return value

    def validate_phone(self, value):
        if value and not re.fullmatch(r"[+0-9][0-9\- ()]{6,19}", value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate(self, attrs):
        if attrs.get("role") == "seller" and not attrs.get("businessName", "").strip():
            raise serializers.ValidationError({"businessName": "Business name is required for sellers."})
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return User.objects.create_user(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"email": "An account with this email already exists."})


class UserSerializer(serializers.ModelSerializer):
    photo = ProfileImageField(
        required=False,
        validators=[validate_profile_image],
    )

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "role", "location", "phone", "address",
            "photo", "businessName", "nidNumber", "bankAccount",
        ]
        read_only_fields = ["id", "email", "role"]

    def validate_phone(self, value):
        if value and not re.fullmatch(r"[+0-9][0-9\- ()]{6,19}", value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    role = serializers.ChoiceField(choices=("buyer", "seller"), required=False, write_only=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["role"] = user.role
        return token

    def validate(self, attrs):
        requested_role = attrs.pop("role", None)
        username = attrs.get(self.username_field)
        password = attrs.get("password")
        user = authenticate(request=self.context.get("request"), username=username, password=password)
        if user and requested_role and user.role != requested_role:
            raise serializers.ValidationError({"role": "This account uses a different account type."})
        data = super().validate(attrs)
        data.update({"username": self.user.username, "role": self.user.role})
        return data


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("The current password is incorrect.")
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context["request"].user)
        return value
