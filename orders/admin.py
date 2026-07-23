from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product_name", "product", "seller", "quantity", "price", "status")
    readonly_fields = ("product_name", "product", "seller", "quantity", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_price", "status", "is_paid", "created_at")
    list_filter = ("status", "is_paid", "payment_method", "created_at")
    list_select_related = ("user",)
    search_fields = ("=id", "user__username", "transaction_id", "stripe_session_id")
    readonly_fields = (
        "total_price", "transaction_id", "stripe_session_id", "payment_method",
        "inventory_reserved", "created_at", "updated_at",
    )
    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product_name", "seller", "quantity", "price", "status")
    list_filter = ("status", "seller")
    list_select_related = ("order", "product", "seller")
    search_fields = ("product_name", "product__name", "=order__id")
