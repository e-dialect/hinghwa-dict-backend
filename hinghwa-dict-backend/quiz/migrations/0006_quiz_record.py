# Generated by Django 3.1.14 on 2023-12-07 08:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0005_paper_record"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuizRecord",
            fields=[
                ("answer", models.CharField(max_length=1000, verbose_name="答案")),
                ("correctness", models.BooleanField(verbose_name="是否正确")),
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
                    "paper",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quiz_paper",
                        to="quiz.paper",
                        verbose_name="所在试卷",
                    ),
                ),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quiz",
                        to="quiz.quiz",
                        verbose_name="测试题",
                    ),
                ),
            ],
        ),
    ]
