from rest_framework.routers import DefaultRouter

from .views import SpecialOfferViewSet


router = DefaultRouter()
router.register("", SpecialOfferViewSet, basename="special-offer")
urlpatterns = router.urls
