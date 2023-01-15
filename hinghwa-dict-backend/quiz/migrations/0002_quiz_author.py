from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("quiz", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="quiz",
            name="author",
            field=models.ForeignKey(
                default=2,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="quizzes",
                to=settings.AUTH_USER_MODEL,
                verbose_name="作者",
            ),
        ),
    ]
