from django.conf import settings
from django.db import models


class SpecialOffer(models.Model):
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="special_offers", null=True, blank=True
    )
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    image = models.ImageField(upload_to="special_offers/", blank=True, default="")
    badge = models.CharField(max_length=100)
    badgeColor = models.CharField(max_length=50, default="bg-emerald-600")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title
