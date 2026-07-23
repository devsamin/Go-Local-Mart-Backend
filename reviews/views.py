from django.db import IntegrityError, transaction
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from localmart_backend.permissions import IsReviewOwnerOrReadOnly
from orders.models import OrderItem
from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsReviewOwnerOrReadOnly]
    http_method_names = ("get", "post", "patch", "delete", "head", "options")
    filterset_fields = ("product", "rating", "user")
    ordering_fields = ("created_at", "rating")

    def get_queryset(self):
        return Review.objects.select_related("user", "product", "order_item")

    def create(self, request, *args, **kwargs):
        order_item_id = request.data.get("order_item")
        try:
            order_item = OrderItem.objects.select_related("product", "order").get(
                id=order_item_id, order__user=request.user
            )
        except (OrderItem.DoesNotExist, ValueError, TypeError):
            raise ValidationError({"order_item": "Choose an item from one of your orders."})
        if order_item.status != "delivered":
            raise ValidationError({"order_item": "Reviews are available after delivery."})
        if order_item.product_id is None:
            raise ValidationError({"order_item": "This product is no longer available."})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                serializer.save(user=request.user, product=order_item.product, order_item=order_item)
        except IntegrityError:
            raise ValidationError({"order_item": "A review already exists for this item."})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
