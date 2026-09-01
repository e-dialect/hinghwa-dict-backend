from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext
from django import forms

from .models import (
    Application,
    Character,
    List,
    Pronunciation,
    SemanticIndexState,
    Word,
)
from website.notification.utils import sendNotification
from utils.admin.widgets import (
    AudioPlayerWidget,
    MarkdownEditorWidget,
    IPAKeyboardWidget,
)


class VerifierListFilter(admin.SimpleListFilter):
    """Custom filter for verifier field with special options."""

    title = "审核人"
    parameter_name = "verifier_status"

    def lookups(self, request, model_admin):
        """Return a list of tuples for filter options."""
        # Get all verifiers who have reviewed items
        from django.contrib.auth.models import User

        verifiers = (
            User.objects.filter(verified_pronunciations__isnull=False).distinct()
            | User.objects.filter(verified_applications__isnull=False).distinct()
        )

        # Build the filter options
        options = [
            ("unreviewed", "未审核"),
            ("reviewed", "已审核（全部）"),
        ]

        # Add individual verifiers
        for verifier in verifiers.distinct():
            options.append((f"user_{verifier.id}", f"{verifier.username}"))

        return options

    def queryset(self, request, queryset):
        """Return the filtered queryset."""
        if self.value() == "unreviewed":
            return queryset.filter(verifier__isnull=True)
        elif self.value() == "reviewed":
            return queryset.filter(verifier__isnull=False)
        elif self.value() and self.value().startswith("user_"):
            user_id = self.value().split("_")[1]
            return queryset.filter(verifier__id=user_id)
        return queryset


# Register your models here.


@admin.register(SemanticIndexState)
class SemanticIndexStateAdmin(admin.ModelAdmin):
    list_display = (
        "status",
        "built_revision",
        "requested_revision",
        "requested_at",
        "completed_at",
    )
    readonly_fields = (
        "singleton_key",
        "status",
        "built_revision",
        "requested_revision",
        "requested_at",
        "started_at",
        "completed_at",
        "lease_owner",
        "lease_expires_at",
        "last_error",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class WordAdminForm(forms.ModelForm):
    """Custom form for Word admin with markdown editor for annotation."""

    class Meta:
        model = Word
        fields = "__all__"
        widgets = {
            "annotation": MarkdownEditorWidget(),
            "standard_ipa": IPAKeyboardWidget(),
            "standard_pinyin": IPAKeyboardWidget(),
        }


class PronunciationAdminForm(forms.ModelForm):
    """Custom form for Pronunciation admin with audio player."""

    class Meta:
        model = Pronunciation
        fields = "__all__"
        widgets = {
            "source": AudioPlayerWidget(),
            "ipa": IPAKeyboardWidget(),
            "pinyin": IPAKeyboardWidget(),
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


class CharacterAdminForm(forms.ModelForm):
    """Custom form for Character admin with IPA keyboard."""

    class Meta:
        model = Character
        fields = "__all__"
        widgets = {
            "ipa": IPAKeyboardWidget(),
            "pinyin": IPAKeyboardWidget(),
        }


class CharacterAdmin(admin.ModelAdmin):
    form = CharacterAdminForm
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
    list_filter = ["contributor", "visibility", "county", VerifierListFilter]
    search_fields = ["word__word", "contributor__username", "pinyin", "id", "ipa"]
    ordering = ["-id", "-views"]
    list_per_page = 50
    raw_id_fields = ("contributor", "word")

    def get_approval_notifications(self, obj):
        """Get approval-related notifications for this pronunciation."""
        from notifications.models import Notification
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(obj)
        # Pronunciation uses action_object field (see word/pronunciation/views.py)
        notifications = Notification.objects.filter(
            action_object_content_type=ct,
            action_object_object_id=obj.id,
            verb__icontains="审核",
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
            # Only send notification if state is actually changing
            if not obj.visibility:
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
                    action_object=obj,
                    title="【通知】语音审核结果",
                )

                self.message_user(
                    request, f"语音 {obj.id} 已审核通过", messages.SUCCESS
                )
            return self._get_next_pronunciation_redirect(request, obj)

        elif "_reject" in request.POST:
            # Reject the pronunciation
            approval_reason = request.POST.get("approval_reason", "").strip()
            # Only send notification if state is actually changing
            if obj.visibility:
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
                    action_object=obj,
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
                    action_object=pro,
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
                content = f"很遗憾，您的语音(id={pro.id}) 没通过审核"
                sendNotification(
                    None,
                    [pro.contributor],
                    content=content,
                    action_object=pro,
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
            "standard_ipa": IPAKeyboardWidget(),
            "standard_pinyin": IPAKeyboardWidget(),
        }


class ApplicationAdmin(admin.ModelAdmin):
    form = ApplicationAdminForm
    change_form_template = "admin/word/application/change_form.html"
    list_display = [
        "id",
        "word",
        "reason",
        "contributor",
        "get_approval_status",
        "verifier",
    ]
    list_filter = ["contributor", VerifierListFilter, "word"]
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
        # For Application, notifications use target (matching existing application/views.py)
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
            # Only process if state is actually changing
            if obj.approved is not True:
                obj.verifier = request.user
                obj.approved = True
                obj.save()

                # Send notification with reason
                content = f"恭喜您的词条申请(id={obj.id}) 已审核通过"
                if approval_reason:
                    content += f"\n\n审核意见：{approval_reason}"
                sendNotification(
                    None,
                    [obj.contributor],
                    content=content,
                    target=obj,
                    title="【通知】词条申请审核结果",
                )

                self.message_user(
                    request, f"词条申请 {obj.id} 已审核通过", messages.SUCCESS
                )
            return self._get_next_application_redirect(request, obj)

        elif "_reject" in request.POST:
            # Reject the application
            approval_reason = request.POST.get("approval_reason", "").strip()
            # Only process if state is actually changing
            if obj.approved is not False:
                obj.verifier = request.user
                obj.approved = False
                obj.save()

                # Send notification with reason
                content = f"很遗憾，您的词条申请(id={obj.id}) 未通过审核"
                if approval_reason:
                    content += f"\n\n审核意见：{approval_reason}"
                sendNotification(
                    None,
                    [obj.contributor],
                    content=content,
                    target=obj,
                    title="【通知】词条申请审核结果",
                )

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

    def get_approval_status(self, obj):
        if obj.approved is True:
            return "已通过"
        if obj.approved is False:
            return "已拒绝"
        if obj.verifier_id is not None:
            return "已审核（历史结果未知）"
        return "待审核"

    get_approval_status.short_description = "审核状态"
    get_approval_status.admin_order_field = "approved"


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
