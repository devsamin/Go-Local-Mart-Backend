from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from products.models import Product
from users.models import User
from .models import Order, OrderItem


class SellerOrderStatusTests(APITestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            "status-seller",
            email="status-seller@example.com",
            password="Strong-pass-123",
            role="seller",
            businessName="Status Shop",
        )
        self.buyer = User.objects.create_user(
            "status-buyer",
            email="status-buyer@example.com",
            password="Strong-pass-123",
            role="buyer",
        )
        self.product = Product.objects.create(
            seller=self.seller,
            name="Tea",
            price=Decimal("100.00"),
            stock=10,
        )
        self.order = Order.objects.create(
            user=self.buyer,
            total_price=Decimal("160.00"),
            status="pending",
            is_paid=True,
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            seller=self.seller,
            product_name=self.product.name,
            quantity=1,
            price=self.product.price,
        )
        unpaid_order = Order.objects.create(
            user=self.buyer,
            total_price=Decimal("160.00"),
            status="awaiting_payment",
            is_paid=False,
        )
        self.unpaid_item = OrderItem.objects.create(
            order=unpaid_order,
            product=self.product,
            seller=self.seller,
            product_name=self.product.name,
            quantity=1,
            price=self.product.price,
        )

    def test_list_returns_paid_orders_and_server_driven_status_options(self):
        self.client.force_authenticate(self.seller)
        response = self.client.get("/api/orders/seller-orders/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual([item["id"] for item in results], [self.item.id])
        self.assertEqual(
            results[0]["available_statuses"],
            [
                {"value": "processing", "label": "Processing"},
                {"value": "shipped", "label": "Shipping"},
                {"value": "delivered", "label": "Delivered"},
                {"value": "cancelled", "label": "Cancelled"},
            ],
        )

    def test_seller_update_is_immediately_visible_in_buyer_order_history(self):
        self.client.force_authenticate(self.seller)
        seller_response = self.client.patch(
            f"/api/orders/seller-orders/{self.item.id}/",
            {"status": "shipped"},
            format="json",
        )

        self.assertEqual(seller_response.status_code, status.HTTP_200_OK)
        self.assertEqual(seller_response.data["status"], "shipped")
        self.assertEqual(
            seller_response.data["available_statuses"],
            [
                {"value": "delivered", "label": "Delivered"},
                {"value": "cancelled", "label": "Cancelled"},
            ],
        )

        self.client.force_authenticate(self.buyer)
        buyer_response = self.client.get("/api/orders/orders/")

        self.assertEqual(buyer_response.status_code, status.HTTP_200_OK)
        buyer_order = next(
            order for order in buyer_response.data["results"] if order["id"] == self.order.id
        )
        self.assertEqual(buyer_order["status"], "shipped")
        self.assertEqual(buyer_order["items"][0]["status"], "shipped")

    def test_seller_cannot_move_an_order_backwards(self):
        self.item.status = "shipped"
        self.item.save(update_fields=["status"])
        self.client.force_authenticate(self.seller)

        response = self.client.patch(
            f"/api/orders/seller-orders/{self.item.id}/",
            {"status": "processing"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "shipped")

    def test_other_seller_cannot_see_or_update_the_order_item(self):
        other_seller = User.objects.create_user(
            "other-status-seller",
            email="other-status-seller@example.com",
            password="Strong-pass-123",
            role="seller",
        )
        self.client.force_authenticate(other_seller)

        list_response = self.client.get("/api/orders/seller-orders/")
        update_response = self.client.patch(
            f"/api/orders/seller-orders/{self.item.id}/",
            {"status": "processing"},
            format="json",
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["results"], [])
        self.assertEqual(update_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_seller_cancellation_restores_stock_and_updates_buyer_history(self):
        original_stock = self.product.stock
        self.client.force_authenticate(self.seller)

        response = self.client.patch(
            f"/api/orders/seller-orders/{self.item.id}/",
            {"status": "cancelled"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")
        self.assertEqual(response.data["available_statuses"], [])
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, original_stock + self.item.quantity)

        self.client.force_authenticate(self.buyer)
        buyer_response = self.client.get("/api/orders/orders/")
        buyer_order = next(
            order for order in buyer_response.data["results"] if order["id"] == self.order.id
        )
        self.assertEqual(buyer_order["status"], "cancelled")
        self.assertEqual(buyer_order["items"][0]["status"], "cancelled")
