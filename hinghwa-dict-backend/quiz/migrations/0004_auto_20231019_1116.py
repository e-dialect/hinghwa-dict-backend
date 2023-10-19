# Generated by Django 3.1.14 on 2023-10-19 03:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("quiz", "0003_quiz_voice_source"),
    ]

    operations = [
        migrations.CreateModel(
            name="Paper",
            fields=[
                (
                    "title",
                    models.CharField(blank=True, max_length=50, verbose_name="试卷标题"),
                ),
                ("quantity", models.IntegerField(blank=True, verbose_name="题目数量")),
                (
                    "id",
                    models.CharField(
                        max_length=20,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="quiz",
            name="type",
            field=models.CharField(blank=True, max_length=50, verbose_name="问题类型"),
        ),
        migrations.CreateModel(
            name="Record",
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
                    "correct_answer",
                    models.IntegerField(blank=True, verbose_name="答对数量"),
                ),
                (
                    "exam",
                    models.ManyToManyField(
                        related_name="exam_record", to="quiz.Paper", verbose_name="答卷记录"
                    ),
                ),
                (
                    "user_answer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="词单作者",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="paper",
            name="quizzes",
            field=models.ManyToManyField(
                blank=True,
                related_name="exam_questions",
                to="quiz.Quiz",
                verbose_name="问题列表",
            ),
        ),
    ]