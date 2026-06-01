from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import UsersViewSet, AuthViewSet

router = DefaultRouter()
router.register(r"users", UsersViewSet, basename="users")
router.register(r"auth", AuthViewSet, basename="auth")

urlpatterns = [
    path("", include(router.urls)),
]
