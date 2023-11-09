from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext

from .models import Word, Character, Pronunciation, Application, List
from website.views import sendNotification


# Register your models here.


class WordAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "word",
        "standard_ipa",
        "standard_pinyin",
        "contributor",
        "views",
        "visibility",
    ]
    list_filter = ["contributor", "visibility"]
    search_fields = [
        "word",
        "definition",
        "contributor__username",
        "id",
        "standard_ipa",
        "standard_pinyin",
    ]
    ordering = ["id", "-views"]
    list_per_page = 50
    filter_horizontal = ["related_words", "related_articles"]
    raw_id_fields = ("contributor",)

    def pass_visibility(self, request, queryset):
        for item in queryset:
            item.visibility = True
            item.save()
        updated = len(queryset)
        self.message_user(
            request,
            ngettext(
                "%d 个词语被成功标记为可见。",
                "%d 个词语被成功标记为可见。",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    pass_visibility.short_description = "所选 词语 通过审核"

    def withdraw_visibility(self, request, queryset):
        for item in queryset:
            item.visibility = False
            item.save()
        updated = len(queryset)
        self.message_user(
            request,
            ngettext(
                "%d 个词语被成功标记为不可见。",
                "%d 个词语被成功标记为不可见。",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    withdraw_visibility.short_description = "所选 词语 不通过审核"

    actions = ["pass_visibility", "withdraw_visibility"]


class CharacterAdmin(admin.ModelAdmin):
    list_display = ["id", "character", "pinyin", "ipa", "traditional", "county", "town"]
    list_filter = ["county"]
    search_fields = [
        "character",
        "pinyin",
        "shengmu",
        "yunmu",
        "shengdiao",
        "ipa",
        "id",
        "traditional",
    ]
    ordering = ["id"]
    list_per_page = 50


class PronunciationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "word",
        "pinyin",
        "ipa",
        "contributor",
        "county",
        "views",
        "visibility",
        "granted",
        "verifier",
    ]
    list_filter = ["contributor", "visibility", "county"]
    search_fields = ["word__word", "contributor__username", "pinyin", "id", "ipa"]
    ordering = ["-id", "-views"]
    list_per_page = 50
    raw_id_fields = ("contributor", "word")

    def pass_visibility(self, request, queryset):
        for pro in queryset:
            if not pro.visibility:
                content = f"恭喜您的语音(id={pro.id}) 已通过审核"
                sendNotification(
                    None,
                    [pro.contributor],
                    content=content,
                    target=pro,
                    title="【通知】语音审核结果",
                )
            pro.visibility = True
            pro.verifier_id = 2
            pro.save()
        updated = len(queryset)
        self.message_user(
            request,
            ngettext(
                "%d 个语音被成功标记为可见。",
                "%d 个语音被成功标记为可见。",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    pass_visibility.short_description = "所选 发音 通过审核"

    def withdraw_visibility(self, request, queryset):
        for pro in queryset:
            if pro.visibility:
                content = f"很遗憾，您的语音(id={id}) 没通过审核"
                sendNotification(
                    None,
                    [pro.contributor],
                    content=content,
                    target=pro,
                    title="【通知】语音审核结果",
                )
            pro.visibility = False
            pro.verifier_id = 2
            pro.save()
        updated = len(queryset)
        self.message_user(
            request,
            ngettext(
                "%d 个语音被成功标记为不可见。",
                "%d 个语音被成功标记为不可见。",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    withdraw_visibility.short_description = "所选 发音 不通过审核"

    actions = ["pass_visibility", "withdraw_visibility"]


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["id", "word", "reason", "contributor", "granted", "verifier"]
    list_filter = ["contributor", "verifier", "word"]
    search_fields = [
        "word__word",
        "content_word",
        "contributor__username",
        "id",
        "definition",
    ]
    ordering = ["-id"]
    list_per_page = 50
    filter_horizontal = ["related_words", "related_articles"]
    raw_id_fields = ("contributor", "verifier", "word")


class WordsInlineAdmin(admin.TabularInline):
    model = List.words.through


class ListsAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "createTime",
        "updateTime",
        "description",
        "author",
        "include_words",
    ]
    list_filter = ["name", "author"]
    search_fields = ["words_word", "name", "description", "author" "id"]
    ordering = ["-id"]
    list_per_page = 50
    # filter_horizontal = ["words_included_word"]
    raw_id_fields = ["words"]
    inlines = (WordsInlineAdmin,)

    def include_words(self, obj):
        return [bt.word for bt in obj.words.all()]


admin.site.register(Word, WordAdmin)
admin.site.register(Character, CharacterAdmin)
admin.site.register(Pronunciation, PronunciationAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(List, ListsAdmin)
