from django.contrib.auth.models import User
from django.db import models


class Music(models.Model):
    source = models.URLField(verbose_name="音乐地址")
    title = models.CharField(max_length=100, verbose_name="曲名")
    artist = models.CharField(max_length=100, verbose_name="作者")
    cover = models.URLField(verbose_name="音乐封面地址")
    likes = models.IntegerField(default=0, verbose_name="点赞数")
    contributor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="musics", verbose_name="贡献者")
    visibility = models.BooleanField(default=False, verbose_name="是否可见")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '音乐'
        verbose_name = '音乐'
