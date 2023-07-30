# Generated by Django 3.1.14 on 2023-07-24 12:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Products",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=100, verbose_name="商品名称"),
                ),
                ("points", models.IntegerField(blank=True, verbose_name="所需积分")),
                ("quantity", models.IntegerField(blank=True, verbose_name="剩余数量")),
                (
                    "picture",
                    models.URLField(
                        blank=True,
                        default="https://cos.edialect.top/website/默认头像.jpg",
                        verbose_name="商品图片",
                    ),
                ),
                (
                    "details",
                    models.TextField(blank=True, max_length=200, verbose_name="商品详情"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Title",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=20, verbose_name="称号"),
                ),
                ("points", models.IntegerField(blank=True, verbose_name="所需积分")),
                (
                    "color",
                    models.CharField(blank=True, max_length=7, verbose_name="颜色"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Transactions",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("timestamp", models.DateTimeField(blank=True, verbose_name="时间")),
                (
                    "action",
                    models.CharField(blank=True, max_length=10, verbose_name="类型"),
                ),
                ("points", models.IntegerField(blank=True, verbose_name="积分数")),
                (
                    "reason",
                    models.CharField(blank=True, max_length=100, verbose_name="原因"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions_user",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
        ),
    ]
