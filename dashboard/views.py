from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from localmart_backend.permissions import IsSeller
from orders.models import OrderItem
from products.models import Product
from reviews.models import Review


class SellerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsSeller]

    def get(self, request):
        orders = OrderItem.objects.filter(seller=request.user, order__is_paid=True)
        revenue = ExpressionWrapper(F("price") * F("quantity"), output_field=DecimalField())
        summary = orders.aggregate(
            total_earnings=Coalesce(Sum(revenue), 0, output_field=DecimalField()),
            products_sold=Coalesce(Sum("quantity"), 0),
            pending=Count("id", filter=Q(status="pending")),
            processing=Count("id", filter=Q(status="processing")),
            shipped=Count("id", filter=Q(status="shipped")),
            completed=Count("id", filter=Q(status="delivered")),
            cancelled=Count("id", filter=Q(status="cancelled")),
        )
        product_summary = Product.objects.filter(seller=request.user).aggregate(
            product_count=Count("id"), low_stock=Count("id", filter=Q(stock__lte=5))
        )
        reviews = Review.objects.filter(product__seller=request.user).select_related("user", "product")
        average_rating = reviews.aggregate(value=Avg("rating"))["value"] or 0

        recent_orders = [
            {
                "id": item.order_id,
                "item_id": item.id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "price": item.price,
                "status": item.status,
                "created_at": item.order.created_at,
            }
            for item in orders.select_related("order").order_by("-order__created_at")[:5]
        ]
        recent_reviews = [
            {
                "customer": review.user.get_full_name() or review.user.username,
                "product": review.product.name,
                "rating": review.rating,
                "comment": review.comment,
                "date": review.created_at,
            }
            for review in reviews[:5]
        ]

        return Response(
            {
                "total_earnings": summary["total_earnings"],
                "products_sold": summary["products_sold"],
                "orders_count": {
                    key: summary[key]
                    for key in ("pending", "processing", "shipped", "completed", "cancelled")
                },
                "product_count": product_summary["product_count"],
                "low_stock_count": product_summary["low_stock"],
                "average_rating": round(average_rating, 1),
                "recent_orders": recent_orders,
                "recent_reviews": recent_reviews,
            }
        )
