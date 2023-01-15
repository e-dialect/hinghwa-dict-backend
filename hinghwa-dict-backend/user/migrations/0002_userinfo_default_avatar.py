from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userinfo",
            name="avatar",
            field=models.URLField(
                blank=True,
                default="https://cos.edialect.top/website/默认头像.jpg",
                verbose_name="头像",
            ),
        ),
    ]
