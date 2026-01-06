from django.contrib import admin
from django_apscheduler.apps import DjangoApschedulerConfig
from django_apscheduler.models import DjangoJob, DjangoJobExecution
from notifications.admin import NotificationAdmin
from notifications.models import Notification
from django import forms
from .models import Website, DailyExpression
from utils.admin.widgets import IPAKeyboardWidget


class WebsiteAdmin(admin.ModelAdmin):
    list_display = ["announcements", "hot_articles", "word_of_the_day", "carousel"]


class DailyExpressionAdminForm(forms.ModelForm):
    """Custom form for DailyExpression admin with IPA keyboard for pinyin."""

    class Meta:
        model = DailyExpression
        fields = "__all__"
        widgets = {
            "pinyin": IPAKeyboardWidget(),
        }


class DailyExpressionAdmin(admin.ModelAdmin):
    form = DailyExpressionAdminForm
    list_display = ["id", "english", "mandarin", "character", "pinyin"]
    list_per_page = 50
    search_fields = ["id", "english", "mandarin", "character", "pinyin"]
    ordering = ("id",)


admin.site.register(Website, WebsiteAdmin)
admin.site.register(DailyExpression, DailyExpressionAdmin)

DjangoApschedulerConfig.verbose_name = "定时任务"
DjangoApschedulerConfig.verbose_name_plural = "定时任务"
DjangoJobExecution._meta.verbose_name_plural = "任务执行情况"
DjangoJobExecution._meta.verbose_name = "任务执行情况"
DjangoJob._meta.verbose_name_plural = "任务"
DjangoJob._meta.verbose_name = "任务"
# 好像没用
Notification._meta.verbose_name_plural = "站内通知"
NotificationAdmin.search_fields = ["recipient__username", "actor__username"]
NotificationAdmin.list_display = list_display = (
    "id",
    "recipient",
    "actor",
    "level",
    "verb",
    "timestamp",
    "unread",
    "public",
)
NotificationAdmin.date_hierarchy = "timestamp"
