from django.db import models


class AuditLogModel(models.Model):
    """操作审计日志 — 记录所有关键操作的详细追溯信息"""

    ACTION_CHOICES = [
        ("create", "创建"),
        ("update", "修改"),
        ("delete", "删除"),
        ("login", "登录"),
        ("logout", "登出"),
        ("sync", "同步"),
        ("connect", "连接"),
        ("other", "其他"),
    ]

    operator = models.CharField(max_length=64, verbose_name="操作人", db_index=True)
    action = models.CharField(
        max_length=16,
        verbose_name="操作类型",
        choices=ACTION_CHOICES,
        db_index=True,
    )
    resource_type = models.CharField(
        max_length=64,
        verbose_name="资源类型",
        db_index=True,
    )
    resource_instance = models.CharField(
        max_length=64,
        verbose_name="资源实例ID",
        db_index=True,
        default="",
        blank=True,
    )
    resource_name = models.CharField(
        max_length=128, verbose_name="资源名称", default="", blank=True
    )
    old_value = models.JSONField(
        verbose_name="变更前值", null=True, blank=True, default=dict
    )
    new_value = models.JSONField(
        verbose_name="变更后值", null=True, blank=True, default=dict
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="操作IP", null=True, blank=True
    )
    request_path = models.CharField(
        max_length=512, verbose_name="请求路径", default="", blank=True
    )
    detail = models.TextField(verbose_name="详细描述", default="", blank=True)
    created_at = models.DateTimeField(
        verbose_name="操作时间", auto_now_add=True, db_index=True
    )

    class Meta:
        db_table = "audit_operation"
        verbose_name = "操作审计日志"
        verbose_name_plural = "操作审计日志"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.get_action_display()}] {self.operator} → {self.resource_type}({self.resource_name}) @ {self.created_at}"
