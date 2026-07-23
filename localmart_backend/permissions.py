from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSeller(BasePermission):
    message = "A seller account is required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "seller")


class IsBuyer(BasePermission):
    message = "A buyer account is required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "buyer")


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or bool(request.user and request.user.is_staff)


class IsSellerOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == "seller")

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.seller_id == request.user.id or request.user.is_staff


class IsReviewOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.user_id == request.user.id or request.user.is_staff
