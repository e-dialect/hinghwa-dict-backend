from django.contrib.auth.models import User
from django.db import models


class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_info',verbose_name='用户')
    nickname = models.CharField(max_length=100, verbose_name='昵称')
    registration_time = models.DateTimeField(auto_now_add=True, verbose_name='注册时间')
    birth = models.DateField(verbose_name='生日')
    phone = models.CharField(max_length=50, verbose_name='电话')
    avatar = models.URLField(verbose_name='头像')
    login_time = models.DateTimeField(verbose_name="最近登录时间")
    county = models.CharField(max_length=100, verbose_name="县区")
    town = models.CharField(max_length=100, verbose_name="乡镇")

