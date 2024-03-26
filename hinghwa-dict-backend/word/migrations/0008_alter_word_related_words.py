from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("word", "0007_character_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="word",
            name="related_words",
            field=models.ManyToManyField(
                blank=True,
                related_name="related_words",
                to="word.word",
                verbose_name="相关词汇",
            ),
        ),
    ]
