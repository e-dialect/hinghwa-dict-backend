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
            name="Article",
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
                    "views",
                    models.IntegerField(
                        default=0, editable=False, verbose_name="阅读量"
                    ),
                ),
                (
                    "publish_time",
                    models.DateTimeField(auto_now_add=True, verbose_name="发布时间"),
                ),
                ("update_time", models.DateTimeField(verbose_name="最近更新时间")),
                ("title", models.CharField(max_length=100, verbose_name="标题")),
                (
                    "description",
                    models.TextField(blank=True, max_length=300, verbose_name="简介"),
                ),
                ("content", models.TextField(verbose_name="正文")),
                ("cover", models.URLField(verbose_name="图片地址")),
                (
                    "visibility",
                    models.BooleanField(default=False, verbose_name="是否审核"),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="articles",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="作者",
                    ),
                ),
                (
                    "like_users",
                    models.ManyToManyField(
                        blank=True,
                        editable=False,
                        related_name="like_articles",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="点赞用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "文章",
                "verbose_name_plural": "文章",
            },
        ),
        migrations.CreateModel(
            name="Comment",
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
                ("content", models.TextField(max_length=500, verbose_name="内容")),
                (
                    "time",
                    models.DateTimeField(auto_now_add=True, verbose_name="评论时间"),
                ),
                (
                    "article",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="article.article",
                        verbose_name="评论文章",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sons",
                        to="article.comment",
                        verbose_name="父评论",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="评论用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "评论",
                "verbose_name_plural": "评论",
            },
        ),
    ]
