from django.contrib import admin

from .models import Word, Character, Pronunciation


# Register your models here.

class WordAdmin(admin.ModelAdmin):
    list_display = ['id', 'word', 'contributor', 'views', 'visibility']
    list_filter = ['contributor', 'visibility']
    search_fields = ['word', 'definition', 'contributor__username']
    ordering = ['id', '-views']
    list_editable = ['visibility']
    list_per_page = 50


class CharacterAdmin(admin.ModelAdmin):
    list_display = ['id', 'pinyin', 'character', 'county', 'town']
    list_filter = ['county']
    search_fields = ['pinyin', 'shengmu', 'yunmu', 'shengdiao']
    ordering = ['id']
    list_per_page = 50


class PronunciationAdmin(admin.ModelAdmin):
    list_display = ['id', 'word', 'pinyin', 'contributor', 'county', 'views', 'visibility']
    list_filter = ['contributor', 'visibility', 'county']
    search_fields = ['word__word', 'contributor__username', 'pinyin']
    ordering = ['id', '-views']
    list_per_page = 50


admin.site.register(Word, WordAdmin)
admin.site.register(Character, CharacterAdmin)
admin.site.register(Pronunciation, PronunciationAdmin)
