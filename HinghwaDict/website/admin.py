from django.contrib import admin

from .models import Website, DailyExpression


class WebsiteAdmin(admin.ModelAdmin):
    list_display = ['announcements', 'hot_articles', 'word_of_the_day', 'carousel']


class DailyExpressionAdmin(admin.ModelAdmin):
    list_display = ['id', 'english', 'mandarin', 'character', 'pinyin']
    list_per_page = 50
    search_fields = ['id', 'english', 'mandarin', 'character', 'pinyin']


admin.site.register(Website, WebsiteAdmin)
admin.site.register(DailyExpression, DailyExpressionAdmin)
