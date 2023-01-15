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
            name="Music",
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
                ("source", models.URLField(verbose_name="音乐地址")),
                ("title", models.CharField(max_length=100, verbose_name="曲名")),
                ("artist", models.CharField(max_length=100, verbose_name="作者")),
                ("cover", models.URLField(verbose_name="音乐封面地址")),
                ("visibility", models.BooleanField(default=False, verbose_name="是否可见")),
                (
                    "contributor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="musics",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="贡献者",
                    ),
                ),
                (
                    "like_users",
                    models.ManyToManyField(
                        blank=True,
                        editable=False,
                        related_name="like_musics",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="点赞用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "音乐",
                "verbose_name_plural": "音乐",
            },
        ),
    ]
