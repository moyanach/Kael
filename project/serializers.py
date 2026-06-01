from rest_framework import serializers

from project.models import BusinessesModel, ProductsModel, ApplicationModel


class BusinessesSerializer(serializers.ModelSerializer):
    """业务线序列化器"""

    class Meta:
        model = BusinessesModel
        fields = [
            "instance", "name", "label", "platform", "description",
            "create_user", "create_at", "update_at",
        ]
        read_only_fields = ["instance", "create_at", "update_at"]


class ProductsSerializer(serializers.ModelSerializer):
    """产品线序列化器"""

    business_name = serializers.CharField(source="business.name", read_only=True)
    business_label = serializers.CharField(source="business.label", read_only=True)

    class Meta:
        model = ProductsModel
        fields = [
            "instance", "name", "label", "description",
            "business", "business_name", "business_label",
            "create_user", "create_at", "update_at",
        ]
        read_only_fields = ["instance", "create_at", "update_at"]

    def to_internal_value(self, data):
        # Support business lookup by instance ID
        result = super().to_internal_value(data)
        return result


class ApplicationSerializer(serializers.ModelSerializer):
    """应用序列化器 (read/list)"""

    owner_username = serializers.CharField(source="owner.username", read_only=True)
    owner_nickname = serializers.CharField(source="owner.nickname", read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True)
    business_label = serializers.CharField(source="business.label", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_label = serializers.CharField(source="product.label", read_only=True)
    lang_display = serializers.CharField(source="get_lang_display", read_only=True)
    level_display = serializers.CharField(source="get_level_display", read_only=True)
    mold_display = serializers.CharField(source="get_mold_display", read_only=True)
    cost_mode_display = serializers.CharField(source="get_cost_mode_display", read_only=True)
    is_docker_display = serializers.CharField(source="get_is_docker_display", read_only=True)

    class Meta:
        model = ApplicationModel
        fields = [
            "instance", "name", "lang", "lang_display",
            "level", "level_display", "mold", "mold_display",
            "cost_mode", "cost_mode_display", "is_docker", "is_docker_display",
            "health", "handle_info", "description",
            "owner", "owner_username", "owner_nickname",
            "business", "business_name", "business_label",
            "product", "product_name", "product_label",
            "create_at", "update_at",
        ]
        read_only_fields = ["instance", "create_at", "update_at"]


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """应用创建序列化器 (write)"""

    class Meta:
        model = ApplicationModel
        fields = [
            "name", "lang", "level", "mold", "cost_mode",
            "is_docker", "health", "handle_info", "description",
            "owner", "business", "product",
        ]

    def create(self, validated_data):
        return ApplicationModel.objects.create(**validated_data)
