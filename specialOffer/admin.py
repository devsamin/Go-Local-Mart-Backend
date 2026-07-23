from django.contrib import admin

from .models import SpecialOffer


@admin.register(SpecialOffer)
class SpecialOfferAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "badge", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    list_select_related = ("seller",)
    search_fields = ("title", "subtitle", "seller__username")
    readonly_fields = ("created_at",)
