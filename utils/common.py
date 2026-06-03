import contextvars
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

# Async-safe context variable to store the current request user
_current_user = contextvars.ContextVar("current_user", default=None)


def get_current_user():
    """Retrieve the current user from context."""
    return _current_user.get()


def set_current_user(user):
    """Set the current user in context."""
    return _current_user.set(user)


class GlobalUserMiddleware:
    """
    Middleware that captures the current logged-in user and stores it in contextvars
    so that it can be accessed in models and signals.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        token = set_current_user(user)
        try:
            response = self.get_response(request)
        finally:
            _current_user.reset(token)
        return response


class CommonFields(models.Model):
    """
    公共字段 — 抽象基类，供其他模型继承。
    注意：id 字段由 Django DEFAULT_AUTO_FIELD 自动管理，不在此显式声明。
    """

    create_by = models.CharField(max_length=64, verbose_name="创建人", default="")
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True


@receiver(pre_save)
def auto_populate_audit_fields(sender, instance, **kwargs):
    """
    Globally listen to pre_save signals and automatically populate create_by/create_user fields
    if they are not already set.
    """
    user = get_current_user()
    username = "system"
    if user and user.is_authenticated:
        username = user.username

    # Set create_by if present and empty
    if hasattr(instance, "create_by") and not getattr(instance, "create_by"):
        instance.create_by = username

    # Set create_user if present and empty
    if hasattr(instance, "create_user") and not getattr(instance, "create_user"):
        instance.create_user = username

