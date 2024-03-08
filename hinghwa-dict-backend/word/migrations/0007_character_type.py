from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("word", "0006_list_ship"),
    ]

    operations = [
        migrations.AddField(
            model_name="character",
            name="type",
            field=models.CharField(max_length=20, null=True, verbose_name="读音类型"),
        ),
    ]
