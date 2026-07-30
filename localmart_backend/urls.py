from django.conf import settings
from django.contrib import admin
from django.http import Http404
from django.urls import include, path
from django.urls import re_path
from django.views.static import serve
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView


def serve_local_media(request, path):
    """Serve bundled legacy media only when explicitly enabled."""
    if not (settings.DEBUG or settings.SERVE_LOCAL_MEDIA):
        raise Http404
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/users/", include("users.urls")),
    path("api/products/", include("products.urls")),
    path("api/cart/", include("cart.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/reviews/", include("reviews.urls")),
    path("api/category/", include("category.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/offers/", include("specialOffer.urls")),
    path("api/payment/", include("payments.urls")),
    re_path(r"^media/(?P<path>.*)$", serve_local_media, name="local-media"),
]
