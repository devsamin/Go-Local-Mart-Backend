from decimal import Decimal
from unittest.mock import patch

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order
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
                    "metadata": {"order_id": str(self.order.id)},
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
        self.assertEqual(self.order.transaction_id, "pi_test")
