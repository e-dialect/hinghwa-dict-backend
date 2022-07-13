from django.contrib.auth.models import User
from django.db import models


class Website(models.Model):
    announcements = models.TextField(verbose_name="本站公告", default="[]")  # list[文章id]
    hot_articles = models.TextField(verbose_name="热门文章", default="[]")  # list[文章id]
    word_of_the_day = models.TextField(verbose_name="每日一词", default="1")  # int
    carousel = models.TextField(verbose_name="精品推荐", default="[]")  # dict{id,source}

    class Meta:
        verbose_name_plural = "网页内容"
        verbose_name = "网页内容"


class DailyExpression(models.Model):
    english = models.CharField(max_length=255, verbose_name="英文表达")
    mandarin = models.CharField(max_length=255, verbose_name="普通话表达")
    character = models.CharField(max_length=255, verbose_name="方言表达")
    pinyin = models.CharField(max_length=255, verbose_name="方言拼音")

    def __str__(self):
        return self.mandarin

    class Meta:
        verbose_name_plural = "日常用语"
        verbose_name = "日常用语"
