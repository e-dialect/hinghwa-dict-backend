from django.contrib.auth.models import User
from django.db import models


class Website(models.Model):
    announcements = models.TextField(verbose_name='本站公告')  # list[文章id]
    hot_articles = models.TextField(verbose_name="热门文章")  # list[文章id]
    word_of_the_day = models.TextField(verbose_name="每日一词")  # int
    carousel = models.TextField(verbose_name="精品推荐")  # dict{id,source}

    class Meta:
        verbose_name_plural = '网页内容'
        verbose_name = '网页内容'


class File(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='所有者')
    name = models.TextField(max_length=100, verbose_name='文件名')
    type = models.CharField(max_length=50, verbose_name='文件类型')
    upload_time = models.TimeField(auto_now_add=True, verbose_name='上传时间')
    local_url = models.URLField(verbose_name='本地访问路径')
    outer_url = models.URLField(blank=True, verbose_name='外网访问路径')
    delete_url = models.URLField(blank=True, verbose_name='删除路径')
