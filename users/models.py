from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    ROLE_CHOICES = (("buyer", "Buyer"), ("seller", "Seller"), ("admin", "Admin"))

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="buyer")
    location = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    address = models.TextField(blank=True, default="")
    photo = models.ImageField(upload_to="profile_photos/", blank=True, default="")
    businessName = models.CharField(max_length=255, blank=True, default="")
    nidNumber = models.CharField(max_length=17, blank=True, default="")
    bankAccount = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("email"), name="unique_user_email_case_insensitive")
        ]

    def __str__(self):
        return f"{self.username} ({self.role})"
