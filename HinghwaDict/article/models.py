from django.contrib.auth.models import User
from django.db import models


class Article(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles', verbose_name='作者')
    views = models.IntegerField(default=0, verbose_name='阅读量')
    like_users = models.ManyToManyField(User, related_name="like_articles", verbose_name="点赞用户")
    publish_time = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")
    update_time = models.DateTimeField(verbose_name="最近更新时间")
    title = models.CharField(max_length=100, verbose_name="标题")
    description = models.TextField(verbose_name="简介", max_length=200)
    content = models.TextField(verbose_name="正文")
    cover = models.URLField(verbose_name="图片地址")

    def __str__(self):
        return self.title

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name="评论用户")
    content = models.TextField(max_length=500, verbose_name="内容")
    time = models.DateTimeField(auto_now_add=True, verbose_name="评论时间")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name="sons", verbose_name="父评论")
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments", verbose_name="评论文章")

    def __str__(self):
        return self.id
