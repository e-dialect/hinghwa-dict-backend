from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("word", "0010_application_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="application",
            name="approved",
            field=models.BooleanField(
                editable=False,
                null=True,
                verbose_name="审核结果",
            ),
        ),
    ]
