from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class CategoryApiTests(APITestCase):
    def test_categories_are_public_but_creation_is_staff_only(self):
        self.assertEqual(self.client.get("/api/category/").status_code, status.HTTP_200_OK)
        seller = User.objects.create_user("seller", email="seller@example.com", password="Strong-pass-123", role="seller")
        self.client.force_authenticate(seller)
        self.assertEqual(
            self.client.post("/api/category/", {"name": "Unsafe"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
