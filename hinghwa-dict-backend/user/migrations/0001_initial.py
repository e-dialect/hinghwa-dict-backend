from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserInfo',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='user_info', serialize=False, to='auth.user', verbose_name='用户')),
                ('wechat', models.CharField(blank=True, max_length=128, verbose_name='微信标识码')),
                ('qq', models.CharField(blank=True, max_length=128, verbose_name='qq标识码')),
                ('nickname', models.CharField(blank=True, max_length=100, verbose_name='昵称')),
                ('birthday', models.DateField(blank=True, default='1970-1-1', verbose_name='生日')),
                ('telephone', models.CharField(blank=True, max_length=50, verbose_name='电话')),
                ('avatar', models.URLField(blank=True, default='https://hinghwadict-1259415432.cos.ap-shanghai.myqcloud.com/files/image/1/2022/01/19/bMuzwU97XtBZHve.jpg', verbose_name='头像')),
                ('county', models.CharField(blank=True, max_length=100, verbose_name='县区')),
                ('town', models.CharField(blank=True, max_length=100, verbose_name='乡镇')),
            ],
            options={
                'verbose_name': '用户详细信息',
                'verbose_name_plural': '用户详细信息',
            },
        ),
    ]
