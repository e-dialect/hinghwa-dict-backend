# Generated by Django 3.1.14 on 2022-03-12 08:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('article', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shengmu', models.CharField(max_length=30, verbose_name='声母')),
                ('ipa', models.CharField(default='', max_length=30, verbose_name='ipa')),
                ('pinyin', models.CharField(max_length=30, verbose_name='拼音')),
                ('yunmu', models.CharField(max_length=30, verbose_name='韵母')),
                ('shengdiao', models.CharField(max_length=10, verbose_name='声调')),
                ('character', models.CharField(max_length=10, verbose_name='汉字')),
                ('county', models.CharField(max_length=100, verbose_name='县区')),
                ('town', models.CharField(max_length=100, verbose_name='乡镇')),
            ],
            options={
                'verbose_name': '单字',
                'verbose_name_plural': '单字',
            },
        ),
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=60, verbose_name='词')),
                ('definition', models.TextField(verbose_name='注释')),
                ('annotation', models.TextField(blank=True, verbose_name='附注')),
                ('mandarin', models.TextField(blank=True, default='[]', verbose_name='对应普通话词语')),
                ('views', models.IntegerField(default=0, editable=False, verbose_name='访问量')),
                ('visibility', models.BooleanField(default=False, verbose_name='是否审核')),
                ('standard_ipa', models.CharField(blank=True, max_length=30, verbose_name='标准IPA')),
                ('standard_pinyin', models.CharField(blank=True, max_length=30, verbose_name='标准拼音')),
                ('contributor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contribute_words', to=settings.AUTH_USER_MODEL, verbose_name='贡献者')),
                ('related_articles', models.ManyToManyField(blank=True, related_name='related_words', to='article.Article', verbose_name='相关帖子')),
                ('related_words', models.ManyToManyField(blank=True, related_name='_word_related_words_+', to='word.Word', verbose_name='相关词汇')),
            ],
            options={
                'verbose_name': '词语',
                'verbose_name_plural': '词语',
            },
        ),
        migrations.CreateModel(
            name='Pronunciation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.URLField(verbose_name='来源')),
                ('ipa', models.CharField(max_length=50, verbose_name='ipa')),
                ('pinyin', models.CharField(max_length=50, verbose_name='拼音')),
                ('county', models.CharField(max_length=100, verbose_name='县区')),
                ('town', models.CharField(max_length=100, verbose_name='乡镇')),
                ('visibility', models.BooleanField(default=False, verbose_name='是否审核')),
                ('views', models.IntegerField(default=0, editable=False, verbose_name='访问量')),
                ('contributor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contribute_pronunciation', to=settings.AUTH_USER_MODEL, verbose_name='贡献者')),
                ('word', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pronunciation', to='word.word', verbose_name='词语')),
            ],
            options={
                'verbose_name': '语音',
                'verbose_name_plural': '语音',
            },
        ),
    ]
