from django.contrib import admin
from django_apscheduler.apps import DjangoApschedulerConfig
from notifications.admin import NotificationAdmin

from .models import Website, DailyExpression


class WebsiteAdmin(admin.ModelAdmin):
    list_display = ['announcements', 'hot_articles', 'word_of_the_day', 'carousel']


class DailyExpressionAdmin(admin.ModelAdmin):
    list_display = ['id', 'english', 'mandarin', 'character', 'pinyin']
    list_per_page = 50
    search_fields = ['id', 'english', 'mandarin', 'character', 'pinyin']
    ordering = ('id',)


admin.site.register(Website, WebsiteAdmin)
admin.site.register(DailyExpression, DailyExpressionAdmin)

DjangoApschedulerConfig.verbose_name = '定时任务'
DjangoApschedulerConfig.verbose_name_plural = '定时任务'
# 好像没用
# Config.verbose_name = '站内通信'
# Config.verbose_name_plural = '站内通信'
NotificationAdmin.search_fields = ['recipient__username', 'actor__username']
NotificationAdmin.list_display = list_display = ('id', 'recipient', 'actor', 'level',
                                                 'verb', 'timestamp', 'unread', 'public')
NotificationAdmin.date_hierarchy = 'timestamp'
