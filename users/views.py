from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from users.models import UsersModel
from users.serializers import UsersSerializer, LoginSerializer
from audit.utils import write_audit_log


class UsersViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """用户管理"""

    queryset = UsersModel.objects.filter(is_delete=False)
    serializer_class = UsersSerializer
    lookup_field = "instance"
    search_fields = ["username", "nickname", "name", "email"]
    ordering_fields = ["username", "name"]

    def get_queryset(self):
        qs = UsersModel.objects.filter(is_delete=False)
        username = self.request.query_params.get("username")
        if username:
            qs = qs.filter(username__icontains=username)
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name__icontains=name)
        return qs


@method_decorator(ensure_csrf_cookie, name="dispatch")
class AuthViewSet(viewsets.GenericViewSet):
    """认证相关接口"""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @action(detail=False, methods=["post"])
    def login(self, request):
        """用户登录"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)
        if user is None:
            # 记录失败登录
            write_audit_log(
                action="login",
                resource_type="User",
                resource_name=username,
                detail=f"用户 {username} 登录失败：密码错误或用户不存在",
                operator=username,
            )
            return Response(
                {"code": 401, "msg": "Invalid credentials", "data": None},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Log the user in to establish the session for SessionAuthentication
        login(request, user)

        # 记录成功登录
        write_audit_log(
            action="login",
            resource_type="User",
            resource_instance=str(user.pk),
            resource_name=user.username,
            detail=f"用户 {user.username} 登录成功",
        )

        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": {"username": user.username, "id": user.pk},
            }
        )
