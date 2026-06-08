"""审计工具函数

提供 write_audit_log 函数，用于手动记录非 CRUD 场景的审计日志，
如：用户登录、Webshell 连接、数据同步等。
"""

from audit.models import AuditLogModel
from utils.common import get_current_user, get_current_request


def write_audit_log(
    action: str,
    resource_type: str,
    resource_instance: str = "",
    resource_name: str = "",
    old_value: dict | None = None,
    new_value: dict | None = None,
    operator: str | None = None,
    ip_address: str | None = None,
    request_path: str = "",
    detail: str = "",
) -> AuditLogModel:
    """手动写入审计日志（用于登录、Webshell、数据同步等非 CRUD 操作）

    参数说明：
        action: 操作类型 (login/logout/sync/connect/other)
        resource_type: 资源类型名称
        resource_instance: 资源实例 ID
        resource_name: 资源名称（展示用）
        old_value: 变更前的值（可选）
        new_value: 变更后的值（可选）
        operator: 操作人（不传则从上下文自动获取）
        ip_address: 操作 IP（不传则从上下文自动获取）
        request_path: 请求路径（不传则从上下文自动获取）
        detail: 详细描述
    """
    if operator is None:
        user = get_current_user()
        operator = user.username if user and user.is_authenticated else "system"

    if ip_address is None or request_path is None:
        request = get_current_request()
        if request:
            if ip_address is None:
                ip = request.META.get("REMOTE_ADDR", "") or request.META.get(
                    "HTTP_X_FORWARDED_FOR", ""
                )
                if "," in ip:
                    ip = ip.split(",")[0].strip()
                ip_address = ip
            if not request_path:
                request_path = request.path

    return AuditLogModel.objects.create(
        operator=operator,
        action=action,
        resource_type=resource_type,
        resource_instance=resource_instance,
        resource_name=resource_name,
        old_value=old_value or {},
        new_value=new_value or {},
        ip_address=ip_address or None,
        request_path=request_path,
        detail=detail,
    )