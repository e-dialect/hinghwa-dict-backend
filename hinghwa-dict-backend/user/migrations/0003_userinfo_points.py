from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0002_userinfo_default_avatar"),
    ]

    operations = [
        migrations.AddField(
            model_name="userinfo",
            name="points_now",
            field=models.IntegerField(default=0, verbose_name="当前积分"),
        ),
        migrations.AddField(
            model_name="userinfo",
            name="points_sum",
            field=models.IntegerField(default=0, verbose_name="总积分"),
        ),
    ]
