from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "seller", "category_names", "price", "stock", "discount", "is_available")
    list_filter = ("categories", "created_at")
    list_select_related = ("seller",)
    search_fields = ("name", "description", "seller__username", "seller__businessName")
    readonly_fields = ("created_at",)
    filter_horizontal = ("categories",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("categories")

    @admin.display(description="Categories")
    def category_names(self, obj):
        return ", ".join(category.name for category in obj.categories.all())
