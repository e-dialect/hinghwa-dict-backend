from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext
from .models import Music


# Register your models here.

class MusicAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'artist', 'contributor', 'like', 'visibility']
    list_filter = ['contributor', 'title', 'visibility']
    search_fields = ['title', 'artist', 'contributor__username', 'id']
    ordering = ['id']
    filter_horizontal = ['like_users']
    raw_id_fields = ("contributor",)
    list_per_page = 50

    def pass_visibility(self, request, queryset):
        for article in queryset:
            article.visibility = True
            article.save()
        updated = len(queryset)
        self.message_user(request, ngettext(
            '%d 个音乐被成功标记为可见。',
            '%d 个音乐被成功标记为可见。',
            updated,
        ) % updated, messages.SUCCESS)

    pass_visibility.short_description = "所选 音乐 通过审核"

    def withdraw_visibility(self, request, queryset):
        for item in queryset:
            item.visibility = False
            item.save()
        updated = len(queryset)
        self.message_user(request, ngettext(
            '%d 个音乐被成功标记为不可见。',
            '%d 个音乐被成功标记为不可见。',
            updated,
        ) % updated, messages.SUCCESS)

    withdraw_visibility.short_description = "所选 音乐 不通过审核"

    actions = ['pass_visibility', 'withdraw_visibility']


admin.site.register(Music, MusicAdmin)
