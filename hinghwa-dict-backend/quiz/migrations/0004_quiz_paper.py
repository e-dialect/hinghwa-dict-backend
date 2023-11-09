from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0003_quiz_voice_source"),
    ]

    operations = [
        migrations.AddField(
            model_name="quiz",
            name="type",
            field=models.CharField(blank=True, max_length=50, verbose_name="问题类型"),
        ),
        migrations.CreateModel(
            name="Paper",
            fields=[
                (
                    "title",
                    models.CharField(blank=True, max_length=50, verbose_name="试卷标题"),
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
                (
                    "quizzes",
                    models.ManyToManyField(
                        blank=True,
                        related_name="exam_questions",
                        to="quiz.Quiz",
                        verbose_name="问题列表",
                    ),
                ),
            ],
        ),
    ]
