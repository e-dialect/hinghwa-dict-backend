from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("word", "0002_pronunciation_upload_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="character",
            name="traditional",
            field=models.CharField(
                blank=True, default="", max_length=30, verbose_name="繁体字"
            ),
        ),
    ]
