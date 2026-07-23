from django.db.models import Avg
from rest_framework import permissions, viewsets
from rest_framework.pagination import PageNumberPagination

from localmart_backend.permissions import IsSellerOwnerOrReadOnly
from .models import Product
from .serializers import ProductSerializer


class ProductPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 60


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsSellerOwnerOrReadOnly]
    pagination_class = ProductPagination
    filterset_fields = {"seller_id": ["exact"], "categories": ["exact"], "stock": ["gt"]}
    search_fields = ("name", "description", "seller__businessName", "seller__location")
    ordering_fields = ("created_at", "price", "stock", "average_rating")
    ordering = ("-created_at",)

    def get_queryset(self):
        return (
            Product.objects.select_related("seller")
            .prefetch_related("categories")
            .annotate(average_rating=Avg("reviews__rating"))
            .distinct()
        )

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
