from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext
from .models import Article, Comment


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'title', 'publish_time', 'update_time', 'views', 'like', 'visibility']
    search_fields = ['author__username', 'title', 'description']
    list_filter = ['author', 'publish_time']
    date_hierarchy = 'publish_time'
    ordering = ('id', 'author__id', '-publish_time', '-views', '-update_time')
    list_editable = ['visibility', ]
    list_per_page = 50
    filter_horizontal = ['like_users']
    def pass_visibility(self, request, queryset):
        for article in queryset:
            article.visibility = True
            article.save()
        updated = len(queryset)
        self.message_user(request, ngettext(
            '%d 篇文章被成功标记为可见。',
            '%d 篇文章被成功标记为可见。',
            updated,
        ) % updated, messages.SUCCESS)
    pass_visibility.short_description = "所选 文章 通过审核"

    def withdraw_visibility(self, request, queryset):
        for article in queryset:
            article.visibility = False
            article.save()
        updated = len(queryset)
        self.message_user(request, ngettext(
            '%d 篇文章被成功标记为不可见。',
            '%d 篇文章被成功标记为不可见。',
            updated,
        ) % updated, messages.SUCCESS)
    withdraw_visibility.short_description = "所选 文章 不通过审核"

    actions = ['pass_visibility', 'withdraw_visibility']


class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'article', 'time']
    list_filter = ['user', 'article']
    search_fields = ['user__username', 'content', 'article__title']
    date_hierarchy = 'time'
    ordering = ['id', '-time']
    list_per_page = 50


admin.site.register(Article, ArticleAdmin)
admin.site.register(Comment, CommentAdmin)
