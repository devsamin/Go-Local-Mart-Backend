import base64
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import User
from localmart_backend.media import optimized_image_url


class FakeCloudinaryStorage:
    def _get_prefix(self):
        return "/media/"


FakeCloudinaryStorage.__module__ = "cloudinary_storage.storage"


class FakeImageField:
    def __init__(self, name, url):
        self.name = name
        self.storage = FakeCloudinaryStorage()
        self._url = url

    def __bool__(self):
        return bool(self.name)

    @property
    def url(self):
        return self._url


class UserApiTests(APITestCase):
    def test_missing_legacy_photo_does_not_generate_a_cloudinary_404_url(self):
        legacy_photo = FakeImageField(
            "profile_photos/c.jpg",
            "https://res.cloudinary.com/example/image/upload/v1/media/profile_photos/c.jpg",
        )

        with tempfile.TemporaryDirectory(dir=settings.BASE_DIR) as media_root, override_settings(
            MEDIA_ROOT=media_root,
            DEBUG=True,
            SERVE_LOCAL_MEDIA=True,
        ):
            self.assertIsNone(optimized_image_url(legacy_photo, width=512))

    def test_real_cloudinary_public_id_gets_an_optimized_url(self):
        cloudinary_photo = FakeImageField(
            "media/profile_photos/session-avatar",
            "https://res.cloudinary.com/example/image/upload/v42/media/profile_photos/session-avatar.jpg",
        )

        self.assertEqual(
            optimized_image_url(cloudinary_photo, width=512),
            "https://res.cloudinary.com/example/image/upload/"
            "f_auto,q_auto,c_limit,w_512/v42/media/profile_photos/session-avatar.jpg",
        )

    def test_registration_with_photo_uses_local_media_in_tests(self):
        image = SimpleUploadedFile(
            "avatar.png",
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
            ),
            content_type="image/png",
        )
        with tempfile.TemporaryDirectory(dir=settings.BASE_DIR) as media_root, override_settings(MEDIA_ROOT=media_root):
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
            self.assertIn("/media/profile_photos/", response.data["photo"])
            self.assertIn("no-store", response["Cache-Control"])

        self.assertTrue(User.objects.filter(username="photo-buyer").exists())

    def test_profile_photo_survives_logout_and_a_fresh_login(self):
        image = SimpleUploadedFile(
            "session-avatar.png",
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
            ),
            content_type="image/png",
        )
        credentials = {
            "username": "returning-buyer",
            "email": "returning-buyer@example.com",
            "password": "Strong-pass-123",
            "role": "buyer",
        }

        with tempfile.TemporaryDirectory(dir=settings.BASE_DIR) as media_root, override_settings(MEDIA_ROOT=media_root):
            registration = self.client.post(
                "/api/users/register/",
                {**credentials, "photo": image},
                format="multipart",
            )
            self.assertEqual(registration.status_code, status.HTTP_201_CREATED)

            first_login = self.client.post(
                "/api/users/login/",
                {"username": credentials["username"], "password": credentials["password"], "role": "buyer"},
                format="json",
            )
            self.assertEqual(first_login.status_code, status.HTTP_200_OK)
            first_client = APIClient()
            first_client.credentials(HTTP_AUTHORIZATION=f"Bearer {first_login.data['access']}")
            first_profile = first_client.get("/api/users/profile/")
            self.assertEqual(first_profile.status_code, status.HTTP_200_OK)
            self.assertIn("session-avatar.png", first_profile.data["photo"])
            self.assertIn("no-store", first_profile["Cache-Control"])
            self.assertIn("Authorization", first_profile["Vary"])

            logout = first_client.post(
                "/api/users/logout/",
                {"refresh": first_login.data["refresh"]},
                format="json",
            )
            self.assertEqual(logout.status_code, status.HTTP_204_NO_CONTENT)

            second_login = APIClient().post(
                "/api/users/login/",
                {"username": credentials["username"], "password": credentials["password"], "role": "buyer"},
                format="json",
            )
            self.assertEqual(second_login.status_code, status.HTTP_200_OK)
            second_client = APIClient()
            second_client.credentials(HTTP_AUTHORIZATION=f"Bearer {second_login.data['access']}")
            second_profile = second_client.get("/api/users/profile/")

            self.assertEqual(second_profile.status_code, status.HTTP_200_OK)
            self.assertEqual(second_profile.data["photo"], first_profile.data["photo"])
            self.assertTrue(User.objects.get(username=credentials["username"]).photo.storage.exists(
                User.objects.get(username=credentials["username"]).photo.name
            ))

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
        with tempfile.TemporaryDirectory(dir=settings.BASE_DIR) as media_root, override_settings(MEDIA_ROOT=media_root):
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
