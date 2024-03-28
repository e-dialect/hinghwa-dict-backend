from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("word", "0008_alter_word_related_words"),
    ]

    operations = [
        migrations.AddField(
            model_name="word",
            name="tags",
            field=models.TextField(blank=True, default="[]", verbose_name="标签"),
        ),
    ]
