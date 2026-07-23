from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order, OrderItem
from products.models import Product
from users.models import User
from .models import Review


class ReviewApiTests(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user("buyer", email="buyer@example.com", password="Strong-pass-123", role="buyer")
        self.seller = User.objects.create_user("seller", email="seller@example.com", password="Strong-pass-123", role="seller")
        self.product = Product.objects.create(seller=self.seller, name="Lamp", price=Decimal("80.00"), stock=2)
        self.order = Order.objects.create(user=self.buyer, total_price=Decimal("140.00"), is_paid=True, status="delivered")
        self.item = OrderItem.objects.create(order=self.order, product=self.product, seller=self.seller, product_name="Lamp", quantity=1, price=Decimal("80.00"), status="delivered")
        self.client.force_authenticate(self.buyer)

    def test_delivered_item_can_be_reviewed_once(self):
        response = self.client.post("/api/reviews/", {"order_item": self.item.id, "rating": 5, "comment": "Excellent"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        duplicate = self.client.post("/api/reviews/", {"order_item": self.item.id, "rating": 4}, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_rating_is_bounded(self):
        response = self.client.post("/api/reviews/", {"order_item": self.item.id, "rating": 6}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_user_cannot_edit_review(self):
        review = Review.objects.create(product=self.product, user=self.buyer, order_item=self.item, rating=4)
        stranger = User.objects.create_user("stranger", email="stranger@example.com", password="Strong-pass-123")
        self.client.force_authenticate(stranger)
        response = self.client.patch(f"/api/reviews/{review.id}/", {"rating": 1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
