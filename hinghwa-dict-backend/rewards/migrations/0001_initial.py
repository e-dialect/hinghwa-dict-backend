from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('name', models.CharField(max_length=100, verbose_name='商品名称')),
                ('points', models.IntegerField(default=0, verbose_name='所需积分')),
                ('quantity', models.IntegerField(default=0, verbose_name='剩余数量')),
                ('picture', models.URLField(default='https://cos.edialect.top/website/默认商品.png', verbose_name='商品图片')),
                ('details', models.TextField(blank=True, max_length=200, verbose_name='商品详情')),
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Title',
            fields=[
                ('name', models.CharField(max_length=20, verbose_name='称号')),
                ('points', models.IntegerField(default=0, verbose_name='所需积分')),
                ('color', models.CharField(default='#000000', max_length=7, verbose_name='颜色')),
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('timestamp', models.DateTimeField(verbose_name='时间')),
                ('action', models.CharField(max_length=10, verbose_name='类型')),
                ('points', models.IntegerField(verbose_name='积分数')),
                ('reason', models.CharField(blank=True, max_length=100, verbose_name='原因')),
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transaction_user', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('address', models.CharField(max_length=100, verbose_name='地址')),
                ('full_name', models.CharField(max_length=10, verbose_name='姓名')),
                ('telephone', models.CharField(max_length=20, verbose_name='电话')),
                ('comment', models.CharField(blank=True, max_length=100, verbose_name='备注')),
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_user', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
        ),
    ]
