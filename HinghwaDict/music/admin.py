from django.contrib import admin

from .models import Music


# Register your models here.

class MusicAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'artist', 'contributor', 'likes', 'visibility']
    list_filter = ['contributor', 'title', 'visibility']
    search_fields = ['title', 'artist', 'contributor__username']
    ordering = ['id', '-likes']
    list_per_page = 50


admin.site.register(Music, MusicAdmin)
