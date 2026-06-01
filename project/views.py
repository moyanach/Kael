# Create your views here.
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from project.models import BusinessesModel, ProductsModel, ApplicationModel
from project.serializers import (
    BusinessesSerializer,
    ProductsSerializer,
    ApplicationSerializer,
    ApplicationCreateSerializer,
)


class BusinessesViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """业务线管理"""

    queryset = BusinessesModel.objects.all()
    serializer_class = BusinessesSerializer
    lookup_field = "instance"
    search_fields = ["name", "label", "platform"]
    ordering_fields = ["create_at", "name"]

    def get_queryset(self):
        qs = BusinessesModel.objects.all()
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name__icontains=name)
        return qs


class ProductsViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """产品线管理"""

    queryset = ProductsModel.objects.all()
    serializer_class = ProductsSerializer
    lookup_field = "instance"
    search_fields = ["name", "label"]
    ordering_fields = ["create_at", "name"]

    def get_queryset(self):
        qs = ProductsModel.objects.select_related("business")
        business = self.request.query_params.get("business")
        if business:
            qs = qs.filter(business__instance=business)
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name__icontains=name)
        return qs


class ApplicationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """应用管理"""

    queryset = ApplicationModel.objects.select_related(
        "owner", "business", "product"
    ).all()
    lookup_field = "instance"
    search_fields = ["name", "lang", "level", "mold"]
    ordering_fields = ["create_at", "name"]

    def get_serializer_class(self):
        if self.action == "create":
            return ApplicationCreateSerializer
        return ApplicationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name__icontains=name)
        business = self.request.query_params.get("business")
        if business:
            qs = qs.filter(business__instance=business)
        product = self.request.query_params.get("product")
        if product:
            qs = qs.filter(product__instance=product)
        lang = self.request.query_params.get("lang")
        if lang:
            qs = qs.filter(lang=lang)
        return qs
