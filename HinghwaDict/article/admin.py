from django.contrib import admin

from .models import Article, Comment


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'title', 'publish_time', 'update_time', 'views', 'like']
    search_fields = ['author__username', 'title', 'description']
    list_filter = ['author', 'publish_time']
    date_hierarchy = 'publish_time'
    ordering = ('id', 'author__id', '-publish_time', '-views', '-update_time')
    list_per_page = 50


class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'article', 'time']
    list_filter = ['user', 'article']
    search_fields = ['user__username', 'content', 'article__title']
    date_hierarchy = 'time'
    ordering = ['id', '-time']
    list_per_page = 50


admin.site.register(Article, ArticleAdmin)
admin.site.register(Comment, CommentAdmin)
