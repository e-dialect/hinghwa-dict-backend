from django.contrib.auth.models import User
from django.db import models

from article.models import Article
import re

# application是为了修改word而产生的
# 所以当word字段发生变化的时候，需要考虑修改application


def split(x: str) -> str:
    return re.sub("([0-9])([^0-9])", "\g<1> \g<2>", re.sub(" *", "", x))


class Word(models.Model):
    word = models.CharField(max_length=60, verbose_name="词")
    definition = models.TextField(verbose_name="注释")
    contributor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="contribute_words",
        verbose_name="贡献者",
    )
    annotation = models.TextField(verbose_name="附注", blank=True)
    mandarin = models.TextField(verbose_name="对应普通话词语", blank=True, default="[]")
    standard_ipa = models.CharField(max_length=100, verbose_name="标准IPA", blank=True)
    standard_pinyin = models.CharField(max_length=100, verbose_name="标准拼音", blank=True)
    views = models.IntegerField(default=0, verbose_name="访问量", editable=False)
    visibility = models.BooleanField(default=False, verbose_name="是否审核")
    related_words = models.ManyToManyField(
        "self", related_name="related_words", verbose_name="相关词汇", blank=True
    )
    related_articles = models.ManyToManyField(
        Article, related_name="related_words", verbose_name="相关帖子", blank=True
    )

    def __str__(self):
        return self.word

    def clean(self):
        self.word = self.word.strip()
        self.definition = self.definition.strip()
        self.annotation = self.annotation.strip()
        if ~isinstance(self.mandarin, str):
            self.mandarin = str(self.mandarin)
        self.mandarin = self.mandarin.strip()
        self.standard_ipa = split(self.standard_ipa)
        self.standard_pinyin = split(self.standard_pinyin)
        return super(Word, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        return super(Word, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "词语"
        verbose_name = "词语"


class Application(models.Model):
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name="关联词条",
        blank=True,
        null=True,
    )
    reason = models.CharField(max_length=200, blank=True, verbose_name="理由")
    contributor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="applications", verbose_name="贡献者"
    )
    verifier = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="verified_applications",
        blank=True,
        null=True,
        verbose_name="审核人",
        editable=False,
    )
    # 修改内容
    content_word = models.CharField(max_length=60, verbose_name="词", blank=True)
    definition = models.TextField(verbose_name="注释", blank=True)
    annotation = models.TextField(verbose_name="附注", blank=True)
    mandarin = models.TextField(verbose_name="对应普通话词语", blank=True, default="[]")
    standard_ipa = models.CharField(max_length=30, verbose_name="标准IPA", blank=True)
    standard_pinyin = models.CharField(max_length=30, verbose_name="标准拼音", blank=True)
    related_words = models.ManyToManyField(
        Word, related_name="related_applications", verbose_name="相关词汇", blank=True
    )
    related_articles = models.ManyToManyField(
        Article, related_name="related_applications", verbose_name="相关帖子", blank=True
    )

    def granted(self):
        return self.verifier is not None

    granted.boolean = True  # admin中添加图标
    granted.short_description = "是否审核"  # 展示名称

    def __str__(self):
        return f"用户{self.contributor.id}" + (
            f"对 {self.word.id} 号词语的修改申请" if self.word else f"的新建词条申请"
        )

    def clean(self):
        self.content_word = self.content_word.strip()
        self.definition = self.definition.strip()
        self.annotation = self.annotation.strip()
        if ~isinstance(self.mandarin, str):
            self.mandarin = str(self.mandarin)
        self.mandarin = self.mandarin.strip()
        self.standard_ipa = split(self.standard_ipa)
        self.standard_pinyin = split(self.standard_pinyin)
        return super(Application, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        return super(Application, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "词语修改申请"
        verbose_name = "词语修改申请"


class Pronunciation(models.Model):
    word = models.ForeignKey(
        Word, on_delete=models.CASCADE, related_name="pronunciation", verbose_name="词语"
    )
    source = models.URLField(verbose_name="来源")
    ipa = models.CharField(max_length=50, verbose_name="ipa")
    pinyin = models.CharField(max_length=50, verbose_name="拼音")
    county = models.CharField(max_length=100, verbose_name="县区")
    town = models.CharField(max_length=100, verbose_name="乡镇")
    contributor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="contribute_pronunciation",
        verbose_name="贡献者",
    )
    visibility = models.BooleanField(default=False, verbose_name="是否可见")
    verifier = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="verified_pronunciations",
        blank=True,
        null=True,
        verbose_name="审核人",
        editable=False,
    )
    views = models.IntegerField(default=0, verbose_name="访问量", editable=False)
    upload_time = models.DateTimeField(
        verbose_name="上传时间", blank=False, null=True, auto_now_add=True
    )

    def granted(self):
        return self.verifier is not None

    granted.boolean = True  # admin中添加图标
    granted.short_description = "是否审核"  # 展示名称

    def clean(self):
        self.ipa = split(self.ipa)
        self.pinyin = split(self.pinyin)
        self.county = self.county.strip()
        self.town = self.town.strip()
        return super(Pronunciation, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        return super(Pronunciation, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "语音"
        verbose_name = "语音"


class Character(models.Model):
    shengmu = models.CharField(max_length=30, verbose_name="声母")
    ipa = models.CharField(max_length=30, verbose_name="ipa", default="")
    pinyin = models.CharField(max_length=30, verbose_name="拼音")
    yunmu = models.CharField(max_length=30, verbose_name="韵母")
    shengdiao = models.CharField(max_length=10, verbose_name="声调")
    character = models.CharField(max_length=10, verbose_name="汉字")
    county = models.CharField(max_length=100, verbose_name="县区")
    town = models.CharField(max_length=100, verbose_name="乡镇")
    traditional = models.CharField(max_length=30, verbose_name="繁体字", default="")

    def clean(self):
        self.shengmu = self.shengmu.strip()
        self.yunmu = self.yunmu.strip()
        self.shengdiao = self.shengdiao.strip()
        self.character = self.character.strip()
        self.pinyin = split(self.pinyin)
        self.ipa = split(self.ipa)
        self.county = self.county.strip()
        self.town = self.town.strip()
        self.traditional = self.traditional.strip()
        return super(Character, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        return super(Character, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "单字"
        verbose_name = "单字"
