from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    location = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    # Buyer/Seller optional fields
    address = models.TextField(blank=True, null=True)
    # photo = models.FileField(upload_to='profile_photos/', blank=True, null=True)

    # ✅ ImageField use
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    businessName = models.CharField(max_length=255, blank=True, null=True)
    nidNumber = models.CharField(max_length=17, blank=True, null=True)
    bankAccount = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"