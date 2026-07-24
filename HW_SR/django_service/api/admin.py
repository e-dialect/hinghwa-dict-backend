from django.contrib import admin

from .models import WordWord


@admin.register(WordWord)
class WordWordAdmin(admin.ModelAdmin):
    list_display = ("id", "word", "views", "visibility", "contributor_id")
    search_fields = ("word", "standard_pinyin", "standard_ipa")
    list_filter = ("visibility",)
