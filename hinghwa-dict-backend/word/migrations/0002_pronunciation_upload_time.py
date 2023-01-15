from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("word", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pronunciation",
            name="upload_time",
            field=models.DateTimeField(
                auto_now_add=True, null=True, verbose_name="上传时间"
            ),
        ),
    ]
