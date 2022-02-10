from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext

from .models import Word, Character, Pronunciation


# Register your models here.


class WordAdmin(admin.ModelAdmin):
    list_display = ['id', 'word', 'contributor', 'views', 'visibility', 'standard_ipa', 'standard_pinyin']
    list_filter = ['contributor', 'visibility']
    search_fields = ['word', 'definition', 'contributor__username']
    ordering = ['id', '-views']
    list_editable = ['visibility']
    list_per_page = 50
    filter_horizontal = ['related_words', 'related_articles']

    def pass_visibility(self, request, queryset):
        for article in queryset:
            article.visibility = True
            article.save()
        updated = len(queryset)
        self.message_user(request, ngettext(
            '%d 个词语被成功标记为可见。',
            '%d 个词语被成功标记为可见。',
            updated,
        ) % updated, messages.SUCCESS)

    pass_visibility.short_description = "所选 词语 通过审核"

    def withdraw_visibility(self, request, queryset):
        for item in queryset:
            item.visibility = False
            item.save()
        updated = len(queryset)
        self.message_user(request, ngettext(
            '%d 个词语被成功标记为不可见。',
            '%d 个词语被成功标记为不可见。',
            updated,
        ) % updated, messages.SUCCESS)

    withdraw_visibility.short_description = "所选 词语 不通过审核"

    actions = ['pass_visibility', 'withdraw_visibility']


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
    list_editable = ['visibility']
    raw_id_fields = ['word']
    list_per_page = 50

    def pass_visibility(self, request, queryset):
        for article in queryset:
            article.visibility = True
            article.save()
        updated = len(queryset)
        self.message_user(request, ngettext(
            '%d 个语音被成功标记为可见。',
            '%d 个语音被成功标记为可见。',
            updated,
        ) % updated, messages.SUCCESS)

    pass_visibility.short_description = "所选 发音 通过审核"

    def withdraw_visibility(self, request, queryset):
        for item in queryset:
            item.visibility = False
            item.save()
        updated = len(queryset)
        self.message_user(request, ngettext(
            '%d 个语音被成功标记为不可见。',
            '%d 个语音被成功标记为不可见。',
            updated,
        ) % updated, messages.SUCCESS)

    withdraw_visibility.short_description = "所选 发音 不通过审核"

    actions = ['pass_visibility', 'withdraw_visibility']


admin.site.register(Word, WordAdmin)
admin.site.register(Character, CharacterAdmin)
admin.site.register(Pronunciation, PronunciationAdmin)
