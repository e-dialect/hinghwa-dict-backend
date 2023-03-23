from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Quiz",
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
                ("question", models.CharField(max_length=100, verbose_name="问题")),
                (
                    "options",
                    models.TextField(blank=True, default="[]", verbose_name="选项"),
                ),
                ("answer", models.IntegerField(default=0, verbose_name="答案序号")),
                ("explanation", models.TextField(verbose_name="答案解析")),
                ("visibility", models.BooleanField(default=False, verbose_name="是否审核")),
            ],
            options={
                "verbose_name": "测试题",
                "verbose_name_plural": "测试题",
            },
        ),
    ]
