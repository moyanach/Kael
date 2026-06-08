from rest_framework import serializers

from audit.models import AuditLogModel


class AuditLogSerializer(serializers.ModelSerializer):
    """审计日志序列化器 — 只读，用于查询展示"""

    action_display = serializers.CharField(
        source="get_action_display", read_only=True
    )

    class Meta:
        model = AuditLogModel
        fields = [
            "id",
            "operator",
            "action",
            "action_display",
            "resource_type",
            "resource_instance",
            "resource_name",
            "old_value",
            "new_value",
            "ip_address",
            "request_path",
            "detail",
            "created_at",
        ]
        read_only_fields = fields