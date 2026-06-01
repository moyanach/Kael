from django.db import models

from utils.tools import generate_instance_id


class UsersModel(models.Model):
    instance = models.CharField(
        max_length=64,
        verbose_name="实例ID",
        unique=True,
        null=False,
        default=generate_instance_id,
    )
    username = models.CharField(max_length=32, verbose_name="用户名", unique=True)
    nickname = models.CharField(max_length=32, verbose_name="花名")
    name = models.CharField(max_length=32, verbose_name="真名", blank=True, default="")
    email = models.CharField(
        max_length=128, verbose_name="邮箱", null=True, blank=True, default=""
    )
    phone = models.CharField(
        max_length=18, verbose_name="电话", null=True, blank=True, default=""
    )
    sex = models.IntegerField(verbose_name="性别", default=1)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)

    class Meta:
        db_table = "users_user"

    def __str__(self) -> str:
        return self.username
