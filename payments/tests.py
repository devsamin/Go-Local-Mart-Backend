from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from products.models import Product
from users.models import User


class PaymentSecurityTests(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user("buyer", email="buyer@example.com", password="Strong-pass-123", role="buyer")
        self.order = Order.objects.create(
            user=self.buyer,
            total_price=Decimal("100.00"),
            status="awaiting_payment",
            inventory_reserved=True,
        )
        self.client.force_authenticate(self.buyer)

    def test_local_health_check_reports_effective_storage_backends(self):
        response = self.client.get("/api/health/")
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["environment"], "local")
        self.assertEqual(payload["database"]["backend"], "sqlite")
        self.assertFalse(payload["database"]["persistent"])
        self.assertFalse(payload["media"]["persistent"])
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_status_endpoint_never_marks_order_paid(self):
        response = self.client.get("/api/payment/status/", {"order_id": self.order.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertFalse(self.order.is_paid)

    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_test")
    @patch("payments.webhooks.stripe.Webhook.construct_event")
    def test_verified_webhook_marks_order_paid(self, construct_event):
        construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test",
                    "payment_status": "paid",
                    "payment_intent": "pi_test",
                    "amount_total": 10000,
                    "currency": "bdt",
                    "metadata": {
                        "order_id": str(self.order.id),
                        "user_id": str(self.buyer.id),
                    },
                }
            },
        }
        response = self.client.post(
            "/api/payment/stripe/webhook/",
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="signed",
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_paid)
        self.assertFalse(self.order.inventory_reserved)
        self.assertEqual(self.order.transaction_id, "pi_test")

    @override_settings(STRIPE_SECRET_KEY="sk_test")
    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_status_securely_reconciles_payment_and_exposes_order_to_seller(self, retrieve):
        seller = User.objects.create_user(
            "seller",
            email="seller@example.com",
            password="Strong-pass-123",
            role="seller",
        )
        product = Product.objects.create(
            seller=seller,
            name="Tea",
            price=Decimal("100.00"),
            stock=4,
        )
        item = OrderItem.objects.create(
            order=self.order,
            product=product,
            seller=seller,
            product_name=product.name,
            quantity=1,
            price=product.price,
        )
        self.order.stripe_session_id = "cs_paid"
        self.order.save(update_fields=["stripe_session_id"])
        retrieve.return_value = {
            "id": "cs_paid",
            "payment_status": "paid",
            "payment_intent": "pi_paid",
            "amount_total": 10000,
            "currency": "bdt",
            "metadata": {
                "order_id": str(self.order.id),
                "user_id": str(self.buyer.id),
            },
        }

        response = self.client.post(
            "/api/payment/stripe/confirm/",
            {"order_id": self.order.id, "session_id": "cs_paid"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["paid"])
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_paid)
        self.assertEqual(self.order.status, "pending")

        self.client.force_authenticate(seller)
        seller_response = self.client.get("/api/orders/seller-orders/")
        self.assertEqual(seller_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [entry["id"] for entry in seller_response.data["results"]],
            [item.id],
        )

    @override_settings(STRIPE_SECRET_KEY="sk_test")
    @patch("payments.views.stripe.checkout.Session.retrieve")
    @patch("payments.views.stripe.checkout.Session.create")
    def test_complete_checkout_flow_reaches_seller_order_list(self, create, retrieve):
        seller = User.objects.create_user(
            "flow-seller",
            email="flow-seller@example.com",
            password="Strong-pass-123",
            role="seller",
        )
        product = Product.objects.create(
            seller=seller,
            name="Coffee",
            price=Decimal("100.00"),
            stock=5,
        )
        cart = Cart.objects.create(user=self.buyer)
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        create.return_value = SimpleNamespace(id="cs_flow", url="https://checkout.test/session")

        checkout_response = self.client.post("/api/orders/orders/checkout/", format="json")
        self.assertEqual(checkout_response.status_code, status.HTTP_201_CREATED)
        order_id = checkout_response.data["order_id"]

        stripe_response = self.client.post(
            "/api/payment/stripe/checkout/",
            {"order_id": order_id},
            format="json",
        )
        self.assertEqual(stripe_response.status_code, status.HTTP_200_OK)
        retrieve.return_value = {
            "id": "cs_flow",
            "payment_status": "paid",
            "payment_intent": "pi_flow",
            "amount_total": 26000,
            "currency": "bdt",
            "metadata": {"order_id": str(order_id), "user_id": str(self.buyer.id)},
        }

        confirmation = self.client.post(
            "/api/payment/stripe/confirm/",
            {"order_id": order_id, "session_id": "cs_flow"},
            format="json",
        )
        self.assertEqual(confirmation.status_code, status.HTTP_200_OK)
        self.assertTrue(confirmation.data["paid"])
        product.refresh_from_db()
        self.assertEqual(product.stock, 3)

        self.client.force_authenticate(seller)
        seller_response = self.client.get("/api/orders/seller-orders/")
        self.assertEqual(seller_response.status_code, status.HTTP_200_OK)
        seller_orders = seller_response.data["results"]
        self.assertEqual(len(seller_orders), 1)
        self.assertEqual(seller_orders[0]["order"], order_id)
        self.assertEqual(seller_orders[0]["product_name"], "Coffee")
        self.assertEqual(seller_orders[0]["quantity"], 2)

    @override_settings(STRIPE_SECRET_KEY="sk_test")
    @patch("payments.views.stripe.checkout.Session.expire")
    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_cancel_expires_stripe_session_before_releasing_inventory(self, retrieve, expire):
        self.order.stripe_session_id = "cs_open"
        self.order.save(update_fields=["stripe_session_id"])
        retrieve.return_value = SimpleNamespace(payment_status="unpaid", status="open")

        response = self.client.post(
            "/api/payment/stripe/cancel/",
            {"order_id": self.order.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expire.assert_called_once_with("cs_open")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cancelled")
        self.assertFalse(self.order.inventory_reserved)
