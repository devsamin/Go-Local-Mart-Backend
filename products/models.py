from django.conf import settings
from decimal import Decimal
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from category.models import Category


class Product(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    discount = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, default="")
    image2 = models.ImageField(upload_to="products/", blank=True, default="")
    image3 = models.ImageField(upload_to="products/", blank=True, default="")
    categories = models.ManyToManyField(Category, related_name="products", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("seller", "-created_at"))]
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gt=0), name="product_price_positive"),
            models.CheckConstraint(
                condition=models.Q(discount__gte=0, discount__lte=99), name="product_discount_valid"
            ),
        ]

    @property
    def is_available(self):
        return self.stock > 0

    @property
    def discounted_price(self):
        return self.price * (100 - self.discount) / 100

    def __str__(self):
        return self.name
