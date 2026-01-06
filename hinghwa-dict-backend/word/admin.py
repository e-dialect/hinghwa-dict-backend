from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext
from django import forms

from .models import Word, Character, Pronunciation, Application, List
from website.views import sendNotification
from utils.admin.widgets import AudioPlayerWidget, MarkdownEditorWidget


# Register your models here.


class WordAdminForm(forms.ModelForm):
    """Custom form for Word admin with markdown editor for annotation."""

    class Meta:
        model = Word
        fields = "__all__"
        widgets = {
            "annotation": MarkdownEditorWidget(),
        }


class PronunciationAdminForm(forms.ModelForm):
    """Custom form for Pronunciation admin with audio player."""

    class Meta:
        model = Pronunciation
        fields = "__all__"
        widgets = {
            "source": AudioPlayerWidget(),
        }


class WordAdmin(admin.ModelAdmin):
    form = WordAdminForm
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
    form = PronunciationAdminForm
    change_form_template = "admin/word/pronunciation/change_form.html"
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
    list_filter = ["contributor", "visibility", "county", "verifier"]
    search_fields = ["word__word", "contributor__username", "pinyin", "id", "ipa"]
    ordering = ["-id", "-views"]
    list_per_page = 50
    raw_id_fields = ("contributor", "word")

    def get_approval_notifications(self, obj):
        """Get approval-related notifications for this pronunciation."""
        from notifications.models import Notification
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(obj)
        notifications = Notification.objects.filter(
            target_content_type=ct, target_object_id=obj.id, verb__icontains="审核"
        ).order_by("-timestamp")

        return notifications

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Add approval notifications to the context."""
        extra_context = extra_context or {}

        if object_id:
            from word.models import Pronunciation

            obj = Pronunciation.objects.get(pk=object_id)
            extra_context["approval_notifications"] = self.get_approval_notifications(
                obj
            )

        return super().change_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        """Handle custom approval buttons on the change form."""
        if "_approve" in request.POST:
            # Approve the pronunciation
            approval_reason = request.POST.get("approval_reason", "").strip()
            if not obj.visibility or obj.verifier != request.user:
                obj.visibility = True
                obj.verifier = request.user
                obj.save()

                # Send notification with reason
                content = f"恭喜您的语音(id={obj.id}) 已通过审核"
                if approval_reason:
                    content += f"\n\n审核意见：{approval_reason}"
                sendNotification(
                    None,
                    [obj.contributor],
                    content=content,
                    target=obj,
                    title="【通知】语音审核结果",
                )

                self.message_user(
                    request, f"语音 {obj.id} 已审核通过", messages.SUCCESS
                )
            return self._get_next_pronunciation_redirect(request, obj)

        elif "_reject" in request.POST:
            # Reject the pronunciation
            approval_reason = request.POST.get("approval_reason", "").strip()
            if obj.visibility or obj.verifier != request.user:
                obj.visibility = False
                obj.verifier = request.user
                obj.save()

                # Send notification with reason
                content = f"很遗憾，您的语音(id={obj.id}) 未通过审核"
                if approval_reason:
                    content += f"\n\n审核意见：{approval_reason}"
                sendNotification(
                    None,
                    [obj.contributor],
                    content=content,
                    target=obj,
                    title="【通知】语音审核结果",
                )

                self.message_user(
                    request, f"语音 {obj.id} 审核不通过", messages.WARNING
                )
            return self._get_next_pronunciation_redirect(request, obj)

        return super().response_change(request, obj)

    def _get_next_pronunciation_redirect(self, request, obj):
        """Redirect to the next pending pronunciation for review."""
        from django.http import HttpResponseRedirect
        from django.urls import reverse

        # Try to find next pending pronunciation (not reviewed yet)
        next_pronunciation = (
            Pronunciation.objects.filter(verifier__isnull=True, id__gt=obj.id)
            .order_by("id")
            .first()
        )

        if next_pronunciation:
            # Redirect to next pending pronunciation
            url = reverse(
                "admin:word_pronunciation_change", args=[next_pronunciation.pk]
            )
            self.message_user(
                request,
                f"已跳转到下一个待审核语音 (ID: {next_pronunciation.id})",
                messages.INFO,
            )
            return HttpResponseRedirect(url)
        else:
            # No more pending, go back to list
            url = reverse("admin:word_pronunciation_changelist")
            self.message_user(request, "没有更多待审核的语音", messages.INFO)
            return HttpResponseRedirect(url)

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


class ApplicationAdminForm(forms.ModelForm):
    """Custom form for Application admin with markdown editor for annotation."""

    class Meta:
        model = Application
        fields = "__all__"
        widgets = {
            "annotation": MarkdownEditorWidget(),
        }


class ApplicationAdmin(admin.ModelAdmin):
    form = ApplicationAdminForm
    change_form_template = "admin/word/application/change_form.html"
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

    def get_approval_notifications(self, obj):
        """Get approval-related notifications for this application."""
        from notifications.models import Notification
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(obj)
        notifications = Notification.objects.filter(
            target_content_type=ct, target_object_id=obj.id, verb__icontains="审核"
        ).order_by("-timestamp")

        return notifications

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Add approval notifications to the context."""
        extra_context = extra_context or {}

        if object_id:
            from word.models import Application

            obj = Application.objects.get(pk=object_id)
            extra_context["approval_notifications"] = self.get_approval_notifications(
                obj
            )

        return super().change_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        """Handle custom approval buttons on the change form."""
        if "_approve" in request.POST:
            # Approve the application
            approval_reason = request.POST.get("approval_reason", "").strip()
            if not obj.verifier or obj.verifier != request.user:
                obj.verifier = request.user
                obj.save()

                # Send notification with reason (if notification system is set up for Application)
                # Currently Application doesn't have notification configured, but keeping the structure
                self.message_user(
                    request, f"词条申请 {obj.id} 已审核通过", messages.SUCCESS
                )
            return self._get_next_application_redirect(request, obj)

        elif "_reject" in request.POST:
            # Reject the application
            # Note: For Application, rejection is indicated by having verifier but no actual approval
            # The system uses notifications to store rejection reasons
            approval_reason = request.POST.get("approval_reason", "").strip()
            if not obj.verifier or obj.verifier != request.user:
                obj.verifier = request.user
                obj.save()

                # Send notification with reason (if notification system is set up)
                self.message_user(
                    request, f"词条申请 {obj.id} 审核不通过", messages.WARNING
                )
            return self._get_next_application_redirect(request, obj)

        return super().response_change(request, obj)

    def _get_next_application_redirect(self, request, obj):
        """Redirect to the next pending application for review."""
        from django.http import HttpResponseRedirect
        from django.urls import reverse

        # Try to find next pending application (not reviewed yet)
        next_application = (
            Application.objects.filter(verifier__isnull=True, id__gt=obj.id)
            .order_by("id")
            .first()
        )

        if next_application:
            # Redirect to next pending application
            url = reverse("admin:word_application_change", args=[next_application.pk])
            self.message_user(
                request,
                f"已跳转到下一个待审核申请 (ID: {next_application.id})",
                messages.INFO,
            )
            return HttpResponseRedirect(url)
        else:
            # No more pending, go back to list
            url = reverse("admin:word_application_changelist")
            self.message_user(request, "没有更多待审核的申请", messages.INFO)
            return HttpResponseRedirect(url)
            url = reverse("admin:word_application_changelist")
            self.message_user(request, "没有更多待审核的申请", messages.INFO)
            return HttpResponseRedirect(url)


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
