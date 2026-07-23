from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from products.models import Product
from localmart_backend.permissions import IsBuyer
from .models import Cart, CartItem
from .serializers import CartMutationSerializer, CartSerializer


class CartViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated, IsBuyer]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related(
            "items__product__seller", "items__product__categories"
        )

    def _cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return self.get_queryset().get(pk=cart.pk)

    def list(self, request, *args, **kwargs):
        return Response(self.get_serializer(self._cart()).data)

    @action(detail=False, methods=("post",))
    def add_item(self, request):
        payload = CartMutationSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        product = get_object_or_404(Product, pk=payload.validated_data["product_id"])
        quantity = payload.validated_data["quantity"]

        with transaction.atomic():
            cart, _ = Cart.objects.select_for_update().get_or_create(user=request.user)
            item = CartItem.objects.select_for_update().filter(cart=cart, product=product).first()
            new_quantity = (item.quantity if item else 0) + quantity
            if new_quantity > product.stock:
                return Response(
                    {"error": f"Only {product.stock} item(s) are currently available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if item:
                item.quantity = new_quantity
                item.save(update_fields=["quantity"])
            else:
                CartItem.objects.create(cart=cart, product=product, quantity=new_quantity)

        return Response({"message": "Cart updated.", "cart": self.get_serializer(self._cart()).data})

    @action(detail=False, methods=("post",))
    def decrease_item(self, request):
        payload = CartMutationSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        cart = self._cart()
        item = get_object_or_404(CartItem, cart=cart, product_id=payload.validated_data["product_id"])
        if item.quantity <= 1:
            item.delete()
        else:
            item.quantity -= 1
            item.save(update_fields=["quantity"])
        return Response({"message": "Cart updated.", "cart": self.get_serializer(self._cart()).data})

    @action(detail=False, methods=("post",))
    def remove_item(self, request):
        payload = CartMutationSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        cart = self._cart()
        deleted, _ = CartItem.objects.filter(
            cart=cart, product_id=payload.validated_data["product_id"]
        ).delete()
        if not deleted:
            return Response({"error": "Item not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Item removed.", "cart": self.get_serializer(self._cart()).data})

    @action(detail=False, methods=("post",))
    def clear(self, request):
        cart = self._cart()
        cart.items.all().delete()
        return Response({"message": "Cart cleared.", "cart": self.get_serializer(self._cart()).data})
