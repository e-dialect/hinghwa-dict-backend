from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("word", "0010_application_tags")]

    operations = [
        migrations.CreateModel(
            name="SemanticIndexState",
            fields=[
                (
                    "singleton_key",
                    models.PositiveSmallIntegerField(
                        default=1, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("requested_revision", models.PositiveBigIntegerField(default=1)),
                ("built_revision", models.PositiveBigIntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "等待构建"),
                            ("building", "构建中"),
                            ("ready", "可用"),
                            ("failed", "构建失败"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("lease_owner", models.CharField(blank=True, max_length=64)),
                (
                    "lease_expires_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("last_error", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "语义检索索引状态",
                "verbose_name_plural": "语义检索索引状态",
                "constraints": [
                    models.CheckConstraint(
                        check=models.Q(("singleton_key", 1)),
                        name="semantic_index_singleton_key_is_one",
                    )
                ],
            },
        )
    ]
