from django.contrib.auth.models import User
from django.db import models

from article.models import Article


class Word(models.Model):
    word = models.CharField(max_length=60, verbose_name="词")
    definition = models.TextField(verbose_name="注释")
    contributor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contribute_words", verbose_name="贡献者")
    annotation = models.TextField(verbose_name="附注", blank=True)
    mandarin = models.TextField(verbose_name="对应普通话词语", blank=True, default='[]')
    related_words = models.ManyToManyField('self', related_name="related_words", verbose_name="相关词汇", blank=True)
    related_articles = models.ManyToManyField(Article, related_name="related_words", verbose_name="相关帖子", blank=True)
    views = models.IntegerField(default=0, verbose_name="访问量")
    visibility = models.BooleanField(default=False, verbose_name='是否审核')
    standard_ipa = models.CharField(max_length=30, verbose_name='标准IPA', blank=True)
    standard_pinyin = models.CharField(max_length=30, verbose_name='标准拼音', blank=True)

    def __str__(self):
        return self.word

    def clean(self):
        self.word = self.word.strip()
        self.definition = self.definition.strip()
        self.annotation = self.annotation.strip()
        self.mandarin = self.mandarin.strip()
        self.standard_ipa = self.standard_ipa.strip()
        self.standard_pinyin = self.standard_pinyin.strip()
        return super(Word, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        return super(Word, self).save(*args, **kwargs)

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
                                    verbose_name="贡献者")
    visibility = models.BooleanField(default=False, verbose_name="是否审核")
    views = models.IntegerField(default=0, verbose_name="访问量")

    def clean(self):
        self.ipa = self.ipa.strip()
        self.pinyin = self.pinyin.strip()
        self.county = self.county.strip()
        self.town = self.town.strip()
        return super(Pronunciation, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        return super(Pronunciation, self).save(*args, **kwargs)

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

    def clean(self):
        self.shengmu = self.shengmu.strip()
        self.yunmu = self.yunmu.strip()
        self.shengdiao = self.shengdiao.strip()
        self.character = self.character.strip()
        self.pinyin = self.pinyin.strip()
        self.ipa = self.ipa.strip()
        self.county = self.county.strip()
        self.town = self.town.strip()
        return super(Character, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        return super(Character, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = '单字'
        verbose_name = '单字'
