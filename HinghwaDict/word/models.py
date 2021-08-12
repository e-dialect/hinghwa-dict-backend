from django.contrib.auth.models import User
from django.db import models

from article.models import Article


class Word(models.Model):
    word = models.CharField(max_length=60, verbose_name="词")
    definition = models.TextField(verbose_name="注释")
    contributor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contribute_words", verbose_name="贡献者",
                                    editable=False)
    annotation = models.TextField(verbose_name="附注", blank=True)
    mandarin = models.TextField(verbose_name="对应普通话词语", blank=True)
    related_words = models.ManyToManyField('self', related_name="related_words", verbose_name="相关词汇", blank=True)
    related_articles = models.ManyToManyField(Article, related_name="related_words", verbose_name="相关帖子", blank=True)
    views = models.IntegerField(default=0, verbose_name="访问量", editable=False)
    visibility = models.BooleanField(default=False, verbose_name='是否审核')

    def __str__(self):
        return self.word

    class Meta:
        verbose_name_plural = '词语'
        verbose_name = '词语'

class Pronunciation(models.Model):
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="pronunciation", verbose_name="词语")
    source = models.URLField(verbose_name="来源")
    ipa = models.CharField(max_length=50, verbose_name="ipa")
    pinyin = models.CharField(max_length=50, verbose_name="拼音")
    county = models.CharField(max_length=100, verbose_name="县区")
    town = models.CharField(max_length=100, verbose_name="乡镇")
    contributor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contribute_pronunciation",
                                    verbose_name="贡献者",editable=False)
    visibility = models.BooleanField(default=False, verbose_name="是否审核")
    views = models.IntegerField(default=0, verbose_name="访问量",editable=False)

    class Meta:
        verbose_name_plural = '语音'
        verbose_name = '语音'


class Character(models.Model):
    shengmu = models.CharField(max_length=30, verbose_name="声母")
    ipa = models.CharField(max_length=30, verbose_name="ipa", default='')
    pinyin = models.CharField(max_length=30, verbose_name="拼音")
    yunmu = models.CharField(max_length=30, verbose_name="韵母")
    shengdiao = models.CharField(max_length=10, verbose_name="声调")
    character = models.CharField(max_length=10, verbose_name="汉字")
    county = models.CharField(max_length=100, verbose_name="县区")
    town = models.CharField(max_length=100, verbose_name="乡镇")

    class Meta:
        verbose_name_plural = '单字'
        verbose_name = '单字'
