from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext
from .models import Quiz


# Register your models here.


class QuizAdmin(admin.ModelAdmin):
    list_display = ["id", "question", "answer", "visibility"]
    list_filter = ["visibility"]
    search_fields = ["id", "question", "answer"]
    ordering = ["id", "question"]
    list_per_page = 50

    def pass_visibility(self, request, queryset):
        for item in queryset:
            item.visibility = True
            item.save()
        updated = len(queryset)
        self.message_user(
            request,
            ngettext(
                "%d 个测试题被成功标记为可见。",
                "%d 个测试题被成功标记为可见。",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    pass_visibility.short_description = "所选 测试题 通过审核"

    def withdraw_visibility(self, request, queryset):
        for item in queryset:
            item.visibility = False
            item.save()
        updated = len(queryset)
        self.message_user(
            request,
            ngettext(
                "%d 个测试题被成功标记为不可见。",
                "%d 个测试题被成功标记为不可见。",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    withdraw_visibility.short_description = "所选 测试题 不通过审核"

    actions = ["pass_visibility", "withdraw_visibility"]


admin.site.register(Quiz, QuizAdmin)
