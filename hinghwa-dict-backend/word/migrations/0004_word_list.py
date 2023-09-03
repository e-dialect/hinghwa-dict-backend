from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("word", "0003_traditional_character"),
    ]

    operations = [
        migrations.AlterField(
            model_name="character",
            name="traditional",
            field=models.CharField(default="", max_length=30, verbose_name="繁体字"),
        ),
        migrations.AlterField(
            model_name="word",
            name="standard_ipa",
            field=models.CharField(blank=True, max_length=100, verbose_name="标准IPA"),
        ),
        migrations.AlterField(
            model_name="word",
            name="standard_pinyin",
            field=models.CharField(blank=True, max_length=100, verbose_name="标准拼音"),
        ),
        migrations.CreateModel(
            name="List",
            fields=[
                (
                    "name",
                    models.CharField(blank=True, max_length=30, verbose_name="类型"),
                ),
                (
                    "id",
                    models.CharField(
                        max_length=20,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("createTime", models.DateTimeField(blank=True, verbose_name="创建时间")),
                ("updateTime", models.DateTimeField(blank=True, verbose_name="更新时间")),
                (
                    "description",
                    models.CharField(blank=True, max_length=100, verbose_name="词单简介"),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="list_words",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="词单作者",
                    ),
                ),
                (
                    "words",
                    models.ManyToManyField(
                        blank=True,
                        related_name="included_word",
                        to="word.Word",
                        verbose_name="词语",
                    ),
                ),
            ],
        ),
    ]
