from django.contrib import admin

from .models import Website


class WebsiteAdmin(admin.ModelAdmin):
    list_display = ['announcements', 'hot_articles', 'word_of_the_day', 'carousel']


admin.site.register(Website, WebsiteAdmin)
