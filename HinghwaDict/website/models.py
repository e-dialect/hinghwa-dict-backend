from django.db import models


class Website(models.Model):
    announcements = models.TextField(verbose_name='本站公告')  # list[文章id]
    hot_articles = models.TextField(verbose_name="热门文章")  # list[文章id]
    word_of_the_day = models.TextField(verbose_name="每日一词")  # int
    carousal = models.TextField(verbose_name="精品推荐")  # dict{id,source}
