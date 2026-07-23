from django.db import models
from django.db.models.functions import Lower

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(Lower("name"), name="unique_category_name_case_insensitive")
        ]

    def __str__(self):
        return self.name
