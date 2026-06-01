from django.db import models


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
