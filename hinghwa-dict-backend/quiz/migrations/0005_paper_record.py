from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("quiz", "0004_quiz_paper"),
    ]

    operations = [
        migrations.CreateModel(
            name="PaperRecord",
            fields=[
                ("timestamp", models.DateTimeField(verbose_name="时间")),
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
                    "examine",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="paper_user",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="答卷人",
                    ),
                ),
                (
                    "paper",
                    models.ForeignKey(
                        blank=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="papers",
                        to="quiz.paper",
                        verbose_name="试卷",
                    ),
                ),
            ],
        ),
    ]
