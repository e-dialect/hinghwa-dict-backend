from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DailyExpression",
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
                ("english", models.CharField(max_length=255, verbose_name="英文表达")),
                (
                    "mandarin",
                    models.CharField(max_length=255, verbose_name="普通话表达"),
                ),
                (
                    "character",
                    models.CharField(max_length=255, verbose_name="方言表达"),
                ),
                ("pinyin", models.CharField(max_length=255, verbose_name="方言拼音")),
            ],
            options={
                "verbose_name": "日常用语",
                "verbose_name_plural": "日常用语",
            },
        ),
        migrations.CreateModel(
            name="Website",
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
                    "announcements",
                    models.TextField(default="[]", verbose_name="本站公告"),
                ),
                (
                    "hot_articles",
                    models.TextField(default="[]", verbose_name="热门文章"),
                ),
                (
                    "word_of_the_day",
                    models.TextField(default="1", verbose_name="每日一词"),
                ),
                ("carousel", models.TextField(default="[]", verbose_name="精品推荐")),
            ],
            options={
                "verbose_name": "网页内容",
                "verbose_name_plural": "网页内容",
            },
        ),
    ]
