import base64
from decimal import Decimal
from pathlib import Path
import tempfile

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from category.models import Category
from localmart_backend.media import optimized_image_url
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

    def test_legacy_media_uses_reachable_backend_url(self):
        image_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        with tempfile.TemporaryDirectory() as media_root, override_settings(
            MEDIA_ROOT=media_root,
            SERVE_LOCAL_MEDIA=True,
        ):
            image_path = Path(media_root, "products", "tea.png")
            image_path.parent.mkdir(parents=True)
            image_path.write_bytes(image_bytes)
            self.product.image.name = "products/tea.png"

            image_url = optimized_image_url(
                self.product.image,
                request=self.client.get("/api/products/").wsgi_request,
            )
            response = self.client.get("/media/products/tea.png")
            response_content = b"".join(response.streaming_content)

        self.assertEqual(image_url, "http://testserver/media/products/tea.png")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_content, image_bytes)
