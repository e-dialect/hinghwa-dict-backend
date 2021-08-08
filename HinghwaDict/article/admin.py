from django.contrib import admin

from .models import Article, Comment


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'title', 'publish_time', 'update_time', 'views', 'like']
    search_fields = ['author', 'title', 'description']
    list_filter = ['author', 'publish_time']
    date_hierarchy = 'publish_time'
    ordering = ('id', 'author__id', '-publish_time', '-views', '-update_time', 'like_users')


class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'article', 'time']
    list_filter = ['user', 'article']
    search_fields = ['user', 'content', 'article']
    date_hierarchy = 'time'
    ordering = ['id', '-time']


admin.site.register(Article, ArticleAdmin)
admin.site.register(Comment, CommentAdmin)
