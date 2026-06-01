from django.urls import path, include
from rest_framework.routers import DefaultRouter

from project.views import BusinessesViewSet, ProductsViewSet, ApplicationViewSet

router = DefaultRouter()
router.register(r"businesses", BusinessesViewSet, basename="businesses")
router.register(r"products", ProductsViewSet, basename="products")
router.register(r"applications", ApplicationViewSet, basename="applications")

urlpatterns = [
    path("", include(router.urls)),
]
