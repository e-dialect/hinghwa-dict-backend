# Generated by Django 3.1.14 on 2023-11-16 08:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('word', '0005_list_admin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='list',
            name='name',
            field=models.CharField(blank=True, max_length=30, verbose_name='词单名称'),
        ),
        migrations.CreateModel(
            name='ListShip',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('li', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='word.list')),
                ('word', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='word.word')),
            ],
            options={
                'verbose_name': '包含词',
                'verbose_name_plural': '包含词',
                'ordering': ['id'],
            },
        ),      
        migrations.RemoveField(
            model_name='list',
            name='words',
        ),
        migrations.AddField(
            model_name='list',
            name='words',
            field=models.ManyToManyField(blank=True, related_name='included_word', through='word.ListShip', to='word.Word', verbose_name='词语'),
        ),
    ]