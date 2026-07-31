import base64
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class UserApiTests(APITestCase):
    def test_registration_with_photo_uses_local_media_in_tests(self):
        image = SimpleUploadedFile(
            "avatar.png",
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
            ),
            content_type="image/png",
        )
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                "/api/users/register/",
                {
                    "username": "photo-buyer",
                    "email": "photo-buyer@example.com",
                    "password": "Strong-pass-123",
                    "role": "buyer",
                    "photo": image,
                },
                format="multipart",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="photo-buyer").exists())

    def test_registration_rejects_admin_role(self):
        response = self.client.post(
            "/api/users/register/",
            {"username": "attacker", "email": "attacker@example.com", "password": "Strong-pass-123", "role": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="attacker").exists())

    def test_seller_requires_business_name(self):
        response = self.client.post(
            "/api/users/register/",
            {"username": "seller", "email": "seller@example.com", "password": "Strong-pass-123", "role": "seller"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_cannot_change_role(self):
        user = User.objects.create_user("buyer", email="buyer@example.com", password="Strong-pass-123", role="buyer")
        self.client.force_authenticate(user)
        response = self.client.patch("/api/users/profile/", {"role": "admin", "location": "Dhaka"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.role, "buyer")
        self.assertEqual(user.location, "Dhaka")

    def test_password_change_checks_current_password(self):
        user = User.objects.create_user("buyer", email="buyer@example.com", password="Strong-pass-123")
        self.client.force_authenticate(user)
        response = self.client.post(
            "/api/users/change-password/", {"current_password": "wrong", "new_password": "New-strong-pass-456"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_patch_replaces_photo_file(self):
        old_image = SimpleUploadedFile(
            "old-avatar.png",
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
            ),
            content_type="image/png",
        )
        new_image = SimpleUploadedFile(
            "new-avatar.png",
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
            ),
            content_type="image/png",
        )
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            user = User.objects.create_user(
                "photo-update",
                email="photo-update@example.com",
                password="Strong-pass-123",
                photo=old_image,
            )
            old_name = user.photo.name
            self.client.force_authenticate(user)

            response = self.client.patch(
                "/api/users/profile/",
                {"photo": new_image},
                format="multipart",
            )
            user.refresh_from_db()
            updated_name = user.photo.name

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(updated_name, old_name)
        self.assertTrue(updated_name.endswith("new-avatar.png"))
        self.assertIn("new-avatar.png", response.data["photo"])
