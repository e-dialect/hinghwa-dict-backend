# Generated migration to add approval_status field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('word', '0010_application_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='approval_status',
            field=models.CharField(
                choices=[
                    ('pending', '待审核'),
                    ('approved', '审核通过'),
                    ('rejected', '审核不通过')
                ],
                default='pending',
                max_length=20,
                verbose_name='审核状态'
            ),
        ),
        migrations.AddField(
            model_name='pronunciation',
            name='approval_status',
            field=models.CharField(
                choices=[
                    ('pending', '待审核'),
                    ('approved', '审核通过'),
                    ('rejected', '审核不通过')
                ],
                default='pending',
                max_length=20,
                verbose_name='审核状态'
            ),
        ),
    ]
