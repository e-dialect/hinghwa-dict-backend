from django.contrib.auth.models import User
from django.db import models


class Transaction(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transaction_user",
        verbose_name="用户",
        editable=True,
    )
    timestamp = models.DateTimeField(verbose_name="时间")
    action = models.CharField(max_length=10, verbose_name="类型")
    points = models.IntegerField(verbose_name="积分数")
    reason = models.CharField(blank=True, max_length=100, verbose_name="原因")
    id = models.CharField(max_length=20, verbose_name="ID", primary_key=True)
