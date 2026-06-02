from rest_framework import serializers

from users.models import UsersModel


class UsersSerializer(serializers.ModelSerializer):
    """用户序列化器"""

    class Meta:
        model = UsersModel
        fields = [
            "instance", "username", "nickname", "name",
            "email", "phone", "sex",
        ]
        read_only_fields = ["instance"]


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
