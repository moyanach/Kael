"""审计信号处理器

通过 Django 信号 (post_save / pre_delete) 自动捕获所有业务模型的 CRUD 操作，
并记录到 AuditLogModel 中。

自动过滤规则：
1. 只审计有 `instance` 字段的模型（即我们自己的 CMDB 业务模型）
2. 排除 Django 内部模型（django.contrib.*）
3. 排除 audit 自身模型，避免无限递归
4. 排除 Sessions 和 Migrations 等内部表
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from audit.models import AuditLogModel
from utils.common import get_current_user


# 需要排除的模型模块前缀 — 不审计 Django 内部和自身
EXCLUDED_MODULES = {
    "django.",
    "audit.",
}


def _should_audit(sender) -> bool:
    """判断是否应该审计该模型"""
    module = getattr(sender, "__module__", "")
    for prefix in EXCLUDED_MODULES:
        if module.startswith(prefix):
            return False
    # 只审计有 instance 字段的模型（CMDB 业务模型特征）
    return hasattr(sender, "instance")


def _get_request_meta():
    """获取当前请求的 IP 和路径（从 context 中）"""
    from utils.common import get_current_request

    request = get_current_request()
    if request is None:
        return None, ""
    ip = request.META.get("REMOTE_ADDR", "") or request.META.get(
        "HTTP_X_FORWARDED_FOR", ""
    )
    if "," in ip:
        ip = ip.split(",")[0].strip()
    return ip, request.path


def _model_to_tracked_dict(instance) -> dict:
    """将模型实例转换为可追踪的字段字典

    排除 AutoField 主键、BinaryField 等不适合记录的大字段，
    外键记录其 instance 值（或 pk 兜底），datetime 序列化为 ISO 格式。
    """
    from django.db import models

    data = {}
    for field in instance._meta.fields:
        # 跳过自增主键
        if field.primary_key and isinstance(field, models.AutoField):
            continue
        # 跳过二进制/文件大字段
        if isinstance(field, (models.BinaryField, models.FileField)):
            continue
        # 跳过 ManyToManyField（不在 _meta.fields 中，但安全起见）
        if isinstance(field, models.ManyToManyField):
            continue

        value = getattr(instance, field.name)

        # 处理外键：记录 instance 值而非对象本身
        if isinstance(field, models.ForeignKey) and value is not None:
            if hasattr(value, "instance"):
                value = str(value.instance)
            else:
                value = str(value.pk)
        # 处理时间字段
        elif hasattr(value, "isoformat"):
            value = value.isoformat()
        # 其余类型转字符串
        elif value is not None and not isinstance(
            value, (str, int, float, bool, list, dict, type(None))
        ):
            value = str(value)

        data[field.name] = value

    return data


def _get_resource_name(instance) -> str:
    """尝试获取实例的名称/标题用于展示"""
    for attr in ("name", "title", "label", "username", "nickname"):
        val = getattr(instance, attr, None)
        if val:
            return str(val)
    return str(instance.pk)


def _write_audit_log(
    *,
    action: str,
    instance,
    old_value: dict | None = None,
    new_value: dict | None = None,
    detail: str = "",
):
    """统一写入审计日志"""
    user = get_current_user()
    operator = user.username if user and user.is_authenticated else "system"
    ip, path = _get_request_meta()

    AuditLogModel.objects.create(
        operator=operator,
        action=action,
        resource_type=instance.__class__.__name__,
        resource_instance=str(getattr(instance, "instance", "")),
        resource_name=_get_resource_name(instance),
        old_value=old_value or {},
        new_value=new_value or {},
        ip_address=ip or None,
        request_path=path,
        detail=detail,
    )


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """自动记录 Create / Update 审计"""
    if not _should_audit(sender):
        return

    action = "create" if created else "update"
    new_value = _model_to_tracked_dict(instance)

    old_value = {}
    if not created:
        # 从数据库重新读取旧值（update 场景）
        try:
            old_obj = sender.objects.get(pk=instance.pk)
            old_value = _model_to_tracked_dict(old_obj)
        except sender.DoesNotExist:
            pass

    _write_audit_log(
        action=action,
        instance=instance,
        old_value=old_value if not created else None,
        new_value=new_value,
    )


@receiver(pre_delete)
def audit_pre_delete(sender, instance, **kwargs):
    """自动记录 Delete 审计"""
    if not _should_audit(sender):
        return

    old_value = _model_to_tracked_dict(instance)
    _write_audit_log(
        action="delete",
        instance=instance,
        old_value=old_value,
        new_value=None,
    )
