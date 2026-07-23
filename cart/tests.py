from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order
from products.models import Product
from users.models import User
from .models import CartItem


class CartAndCheckoutTests(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user("buyer", email="buyer@example.com", password="Strong-pass-123", role="buyer")
        self.seller = User.objects.create_user("seller", email="seller@example.com", password="Strong-pass-123", role="seller")
        self.product = Product.objects.create(seller=self.seller, name="Basket", price=Decimal("100.00"), stock=5)
        self.client.force_authenticate(self.buyer)

    def add_item(self, quantity=1):
        return self.client.post(
            "/api/cart/add_item/", {"product_id": self.product.id, "quantity": quantity}, format="json"
        )

    def test_cart_does_not_reduce_inventory(self):
        response = self.add_item(2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(response.data["cart"]["item_count"], 2)

    def test_checkout_reserves_stock_snapshots_price_and_clears_cart(self):
        self.add_item(2)
        response = self.client.post("/api/orders/orders/checkout/", format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(pk=response.data["order_id"])
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(order.total_price, Decimal("260.00"))
        self.assertTrue(order.inventory_reserved)
        self.assertEqual(order.items.get().product_name, "Basket")
        self.assertFalse(CartItem.objects.filter(cart__user=self.buyer).exists())

    def test_cancelling_unpaid_checkout_restores_stock_and_cart(self):
        self.add_item(2)
        order_id = self.client.post("/api/orders/orders/checkout/", format="json").data["order_id"]
        response = self.client.post(f"/api/orders/orders/{order_id}/cancel/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        order = Order.objects.get(pk=order_id)
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(order.status, "cancelled")
        self.assertFalse(order.inventory_reserved)
        self.assertEqual(CartItem.objects.get(cart__user=self.buyer).quantity, 2)

    def test_seller_cannot_use_buyer_cart(self):
        self.client.force_authenticate(self.seller)
        response = self.client.get("/api/cart/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
