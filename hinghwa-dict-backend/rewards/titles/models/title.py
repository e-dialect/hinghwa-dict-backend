from django.db import models


class Title(models.Model):
    name = models.CharField(max_length=20, verbose_name="称号")
    points = models.IntegerField(verbose_name="所需积分", default=0)
    color = models.CharField(max_length=7, verbose_name="颜色", default="#000000")
    id = models.CharField(max_length=20, verbose_name="ID", primary_key=True)

    def __str__(self):
        return self.name
