from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="商品名称")
    points = models.IntegerField(verbose_name="所需积分", default=0)
    quantity = models.IntegerField(verbose_name="剩余数量", default=0)
    picture = models.URLField(
        default="https://cos.edialect.top/website/默认商品.png",
        verbose_name="商品图片",
    )
    details = models.TextField(blank=True, max_length=200, verbose_name="商品详情")
    id = models.CharField(max_length=20, verbose_name="ID", primary_key=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "商品"
        verbose_name = "商品"
