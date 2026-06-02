from django.db import models

from users.models import UsersModel
from project.constant import *
from utils.common import CommonFields
from utils.tools import generate_instance_id


class BusinessesModel(CommonFields):
    instance = models.CharField(
        max_length=64,
        verbose_name="实例ID",
        unique=True,
        null=False,
        default=generate_instance_id,
    )
    name = models.CharField(max_length=32, verbose_name="业务线名称")
    label = models.CharField(max_length=32, verbose_name="业务线别名")
    platform = models.CharField(max_length=32, verbose_name="业务线平台", choices=platform_type)
    description = models.CharField(max_length=255, verbose_name="业务线描述", default="")
    create_user = models.CharField(max_length=64, verbose_name="创建人", default="")

    class Meta(CommonFields.Meta):
        db_table = "apps_business"

    def __str__(self) -> str:
        return self.name


class ProductsModel(models.Model):
    instance = models.CharField(
        max_length=64,
        verbose_name="实例ID",
        unique=True,
        null=False,
        default=generate_instance_id,
    )
    name = models.CharField(max_length=32, verbose_name="产品线名称")
    label = models.CharField(max_length=32, verbose_name="产品线别名")
    description = models.CharField(max_length=255, verbose_name="产品线描述")
    business = models.ForeignKey(
        BusinessesModel,
        to_field="instance",
        on_delete=models.CASCADE,
        related_name="business_product",
        verbose_name="业务线ID",
    )
    create_user = models.CharField(max_length=64, verbose_name="创建人", default="")

    class Meta(CommonFields.Meta):
        db_table = "apps_product"

    def __str__(self) -> str:
        return self.name


class ApplicationModel(CommonFields):
    instance = models.CharField(
        max_length=64,
        verbose_name="实例ID",
        unique=True,
        null=False,
        default=generate_instance_id,
    )
    name = models.CharField(max_length=64, verbose_name="应用名")
    lang = models.CharField(verbose_name="语言", max_length=18, choices=lang_choice)
    level = models.CharField(verbose_name="应用等级", max_length=8, choices=app_level_choice)
    mold = models.CharField(verbose_name="应用类型", max_length=18, choices=app_type_choice)
    cost_mode = models.CharField(verbose_name="成本模型", max_length=18, choices=app_cost_choice)
    is_docker = models.CharField(verbose_name="容器应用", max_length=18, choices=docker_type_choice)
    health = models.JSONField(verbose_name="巡检健康度信息", null=True, default=dict)
    handle_info = models.CharField(verbose_name="服务健康度处理意见", max_length=300, null=True, default="")
    description = models.CharField(verbose_name="备注信息", max_length=255, default="")
    # 用户删除，允许owner为空， 必须有补偿机制确保该字段及时有值
    owner = models.ForeignKey(
        UsersModel,
        on_delete=models.SET_NULL,
        related_name="owner_set",
        to_field="instance",
        null=True,
    )
    # 业务线删除，允许该字段短暂为空， 必须有补偿机制确保该字段及时有值
    business = models.ForeignKey(
        BusinessesModel,
        on_delete=models.SET_NULL,
        related_name="business_set",
        to_field="instance",
        null=True,
    )
    # 产品线删除，允许该字段短暂为空， 必须有补偿机制确保该字段及时有值
    product = models.ForeignKey(
        ProductsModel,
        on_delete=models.SET_NULL,
        related_name="product_set",
        to_field="instance",
        null=True,
    )

    class Meta(CommonFields.Meta):
        db_table = "apps_application"

    def __str__(self) -> str:
        return self.name
