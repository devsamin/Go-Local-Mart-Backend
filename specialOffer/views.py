from rest_framework import permissions, viewsets
from django.db.models import Q

from localmart_backend.permissions import IsSellerOwnerOrReadOnly
from .models import SpecialOffer
from .serializers import SpecialOfferSerializer


class SpecialOfferViewSet(viewsets.ModelViewSet):
    serializer_class = SpecialOfferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsSellerOwnerOrReadOnly]
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def get_queryset(self):
        queryset = SpecialOffer.objects.select_related("seller")
        if self.request.user.is_authenticated and self.request.user.role == "seller":
            queryset = queryset.filter(Q(is_active=True) | Q(seller=self.request.user))
        else:
            queryset = queryset.filter(is_active=True)
        return queryset

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
