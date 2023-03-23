from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0002_quiz_author"),
    ]

    operations = [
        migrations.AddField(
            model_name="quiz",
            name="voice_source",
            field=models.URLField(default="", verbose_name="播报语音链接"),
        ),
    ]
