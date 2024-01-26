from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("quiz", "0006_quiz_record"),
    ]

    operations = [
        migrations.AlterField(
            model_name="quizrecord",
            name="paper",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="quiz_paper",
                to="quiz.paperrecord",
                verbose_name="所在答卷记录",
            ),
        ),
        migrations.CreateModel(
            name="Cert",
            fields=[
                ("level", models.IntegerField(verbose_name="等级")),
                ("name", models.CharField(max_length=20, verbose_name="参与者")),
                ("place", models.CharField(max_length=100, verbose_name="地址")),
                ("sequence", models.IntegerField(verbose_name="第几次认证")),
                ("grade", models.CharField(max_length=20, verbose_name="等级")),
                (
                    "scores",
                    models.TextField(blank=True, default="[]", verbose_name="分数"),
                ),
                ("time", models.DateTimeField(max_length=20, verbose_name="时间")),
                (
                    "id",
                    models.CharField(
                        max_length=20,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cert_user",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="证书用户",
                    ),
                ),
            ],
        ),
    ]
