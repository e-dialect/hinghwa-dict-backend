from django.db import models
from django.contrib.auth.models import User
import uuid


class Products(models.Model):
    name = models.CharField(blank=True, max_length=100, verbose_name="商品名称")
    points = models.IntegerField(blank=True, verbose_name="所需积分")
    quantity = models.IntegerField(blank=True, verbose_name="剩余数量")
    picture = models.URLField(
        default="https://cos.edialect.top/website/默认头像.jpg",
        blank=True,
        verbose_name="商品图片",
    )
    details = models.TextField(blank=True, max_length=200, verbose_name="商品详情")
    id = models.CharField(blank=True, max_length=20, verbose_name="ID", primary_key=True)

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(blank=True, max_length=20, verbose_name="称号")
    points = models.IntegerField(blank=True, verbose_name="所需积分")
    color = models.CharField(blank=True, max_length=7, verbose_name="颜色")
    id = models.CharField(blank=True, max_length=20, verbose_name="ID",primary_key=True)

    def __str__(self):
        return self.name


class Transactions(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transactions_user",
        verbose_name="用户",
        editable=True
    )
    timestamp = models.DateTimeField(blank=True, verbose_name="时间")
    action = models.CharField(blank=True, max_length=10, verbose_name="类型")
    points = models.IntegerField(blank=True, verbose_name="积分数")
    reason = models.CharField(blank=True,max_length=100, verbose_name="原因")
    id = models.CharField(blank=True, max_length=20, verbose_name="ID", primary_key=True)


class Orders(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders_user",
        verbose_name="用户",
        editable=True
    )
    address = models.CharField(blank=True, max_length=100, verbose_name="地址")
    full_name = models.CharField(blank=True, max_length=10, verbose_name="姓名")
    telephone = models.CharField(blank=True, max_length=20, verbose_name="电话")
    comment = models.CharField(blank=True, max_length=100, verbose_name="备注")
    id = models.CharField(blank=True, max_length=20, verbose_name="ID", primary_key=True)
