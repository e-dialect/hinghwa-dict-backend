from django.contrib.auth.models import User
from django.db import models


class Order(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="order_user",
        verbose_name="用户",
        editable=True,
    )
    address = models.CharField(max_length=100, verbose_name="地址")
    full_name = models.CharField(max_length=10, verbose_name="姓名")
    telephone = models.CharField(max_length=20, verbose_name="电话")
    comment = models.CharField(blank=True, max_length=100, verbose_name="备注")
    id = models.CharField(max_length=20, verbose_name="ID", primary_key=True)

    class Meta:
        verbose_name_plural = "订单"
        verbose_name = "订单"
