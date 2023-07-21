from django.contrib.auth.models import User
from django.db import models


class UserInfo(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="user_info",
        verbose_name="用户",
        primary_key=True,
    )
    wechat = models.CharField(
        max_length=128, blank=True, verbose_name="微信标识码"
    )  # openid
    qq = models.CharField(max_length=128, blank=True, verbose_name="qq标识码")  # openid
    nickname = models.CharField(blank=True, max_length=100, verbose_name="昵称")
    birthday = models.DateField(blank=True, default="1970-1-1", verbose_name="生日")
    telephone = models.CharField(blank=True, max_length=50, verbose_name="电话")
    avatar = models.URLField(
        default="https://cos.edialect.top/website/默认头像.jpg",
        blank=True,
        verbose_name="头像",
    )
    county = models.CharField(blank=True, max_length=100, verbose_name="县区")
    town = models.CharField(blank=True, max_length=100, verbose_name="乡镇")
    points_sum = models.IntegerField(default=0, verbose_name="总积分")
    points_now = models.IntegerField(default=0, verbose_name="当前积分")
    reasons = models.TextField(blank=True, verbose_name="积分变动原因")
    timestamps = models.TextField(blank=True, verbose_name="积分变动时间戳")
    title = models.CharField(blank=True, max_length=50, verbose_name="头衔")
    color = models.CharField(
        blank=True, max_length=7, default="#000000", verbose_name="字体颜色"
    )

    def add(self, reason, timestamp):
        if not self.reasons:
            self.reasons = reason
            self.timestamps = timestamp
        else:
            self.reasons += f"\n{reason}"
            self.timestamps += f"\n{timestamp}"
        self.save()

    def combine(self):
        reasons = self.reasons.splitlines() if self.reasons else []
        timestamps = self.timestamps.splitlines() if self.timestamps else []
        return list(zip(reasons, timestamps))

    def __str__(self):
        return self.user.username

    def ID(self):
        return self.user.id

    class Meta:
        verbose_name_plural = "用户详细信息"
        verbose_name = "用户详细信息"
