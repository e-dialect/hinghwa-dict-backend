from django.db import models


class Rewards(models.Model):
    name = models.CharField(blank=True, max_length=100, verbose_name="商品名称")
    point = models.IntegerField(blank=True, verbose_name="所需积分")
    left = models.IntegerField(blank=True, verbose_name="剩余数量")
    picture = models.URLField(
        default="https://cos.edialect.top/website/默认头像.jpg",
        blank=True,
        verbose_name="商品图片",
    )
    detail = models.TextField(blank=True, max_length=200, verbose_name="商品详情")

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(blank=True, max_length=20, verbose_name="称号")
    point = models.IntegerField(blank=True, verbose_name="所需积分")
    color = models.CharField(blank=True, max_length=7, verbose_name="颜色")
    owned = models.CharField(blank=True, max_length=10, verbose_name="是否拥有")

    def __str__(self):
        return self.name
