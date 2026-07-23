from rest_framework import generics

from localmart_backend.permissions import IsAdminOrReadOnly
from .models import Category
from .serializers import CategorySerializer


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
