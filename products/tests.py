from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from category.models import Category
from users.models import User
from .models import Product


class ProductApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user("seller", email="seller@example.com", password="Strong-pass-123", role="seller")
        self.other = User.objects.create_user("other", email="other@example.com", password="Strong-pass-123", role="seller")
        self.category = Category.objects.create(name="Groceries")
        self.product = Product.objects.create(seller=self.owner, name="Tea", price=Decimal("100.00"), stock=5)
        self.product.categories.add(self.category)

    def test_public_list_is_paginated_and_searchable(self):
        response = self.client.get("/api/products/", {"search": "Tea"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Tea")

    def test_only_owner_can_change_product(self):
        self.client.force_authenticate(self.other)
        response = self.client.patch(f"/api/products/{self.product.id}/", {"stock": 2})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.owner)
        response = self.client.patch(f"/api/products/{self.product.id}/", {"stock": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)

    def test_buyer_cannot_create_product(self):
        buyer = User.objects.create_user("buyer", email="buyer@example.com", password="Strong-pass-123", role="buyer")
        self.client.force_authenticate(buyer)
        response = self.client.post(
            "/api/products/",
            {"name": "Rice", "price": "40.00", "discount": 0, "stock": 10, "category_ids": [self.category.id]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_discount_validation_prevents_free_product(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(f"/api/products/{self.product.id}/", {"discount": 100})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
