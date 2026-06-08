from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from audit.models import AuditLogModel
from audit.serializers import AuditLogSerializer


class AuditLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """操作审计日志 — 只读查询接口

    支持按操作人、操作类型、资源类型、资源名称、时间范围过滤。
    默认按操作时间倒序排列。
    """

    queryset = AuditLogModel.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ["created_at", "operator", "action", "resource_type"]
    search_fields = ["operator", "resource_name", "detail"]
    filterset_fields = ["action", "resource_type"]

    def get_queryset(self):
        qs = AuditLogModel.objects.all()

        # 操作人过滤
        operator = self.request.query_params.get("operator")
        if operator:
            qs = qs.filter(operator__icontains=operator)

        # 操作类型过滤
        action = self.request.query_params.get("action")
        if action:
            qs = qs.filter(action=action)

        # 资源类型过滤
        resource_type = self.request.query_params.get("resource_type")
        if resource_type:
            qs = qs.filter(resource_type__icontains=resource_type)

        # 资源名称搜索
        resource_name = self.request.query_params.get("resource_name")
        if resource_name:
            qs = qs.filter(resource_name__icontains=resource_name)

        # 时间范围过滤
        start_time = self.request.query_params.get("start_time")
        if start_time:
            qs = qs.filter(created_at__gte=start_time)
        end_time = self.request.query_params.get("end_time")
        if end_time:
            qs = qs.filter(created_at__lte=end_time)

        # 排序
        ordering = self.request.query_params.get("ordering", "-created_at")
        if ordering.lstrip("-") in self.ordering_fields:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("-created_at")

        return qs