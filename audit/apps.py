from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'

    def ready(self):
        """导入信号处理器，使其在 Django 启动时注册"""
        import audit.signals  # noqa