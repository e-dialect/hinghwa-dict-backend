from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("word", "0009_word_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="application",
            name="tags",
            field=models.TextField(blank=True, default="[]", verbose_name="标签"),
        ),
    ]
