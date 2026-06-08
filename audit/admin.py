from django.contrib import admin

from audit.models import AuditLogModel


@admin.register(AuditLogModel)
class AuditLogAdmin(admin.ModelAdmin):
    """审计日志后台管理"""

    list_display = [
        "created_at",
        "operator",
        "action",
        "resource_type",
        "resource_name",
        "ip_address",
    ]
    list_filter = ["action", "resource_type", "created_at"]
    search_fields = ["operator", "resource_name", "resource_instance"]
    readonly_fields = [
        "operator",
        "action",
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
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False