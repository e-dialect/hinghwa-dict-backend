from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext
from django import forms
from django.shortcuts import redirect
from django.urls import reverse
from .models import Article, Comment
from utils.admin.widgets import MarkdownEditorWidget, ImagePreviewWidget
from website.notification.utils import sendNotification


class ArticleAdminForm(forms.ModelForm):
    """Custom form for Article admin with markdown editor and image preview."""

    class Meta:
        model = Article
        fields = "__all__"
        widgets = {
            "content": MarkdownEditorWidget(),
            "cover": ImagePreviewWidget(),
        }


class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    change_form_template = "admin/article/article/change_form.html"
    list_display = [
        "id",
        "author",
        "title",
        "publish_time",
        "update_time",
        "views",
        "like",
        "visibility",
    ]
    search_fields = ["author__username", "title", "description", "id"]
    list_filter = ["author", "publish_time", "visibility"]
    date_hierarchy = "publish_time"
    ordering = ("id", "author__id", "-publish_time", "-views", "-update_time")
    list_per_page = 50
    filter_horizontal = ["like_users"]
    raw_id_fields = ("author",)

    def get_approval_notifications(self, obj):
        """Get approval-related notifications for this article."""
        from notifications.models import Notification
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(obj)
        # Article uses action_object field (see article/views.py)
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
            from article.models import Article

            obj = Article.objects.get(pk=object_id)
            extra_context["approval_notifications"] = self.get_approval_notifications(
                obj
            )

        return super().change_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        """Handle custom approval buttons on the change form."""
        if "_approve" in request.POST:
            # Approve the article
            approval_reason = request.POST.get("approval_reason", "").strip()
            if not obj.visibility:
                obj.visibility = True
                obj.save()

                # Send notification with reason
                content = f"恭喜您的文章(id={obj.id}) 已通过审核"
                if approval_reason:
                    content += f"\n\n审核意见：{approval_reason}"
                sendNotification(
                    None,
                    [obj.author],
                    content=content,
                    action_object=obj,
                    title="【通知】文章审核结果",
                )

                self.message_user(
                    request, f"文章 {obj.id} 已审核通过", messages.SUCCESS
                )
            return self._get_next_article_redirect(request, obj)

        elif "_reject" in request.POST:
            # Reject the article
            approval_reason = request.POST.get("approval_reason", "").strip()
            if obj.visibility:
                obj.visibility = False
                obj.save()

                # Send notification with reason
                content = f"很遗憾，您的文章(id={obj.id}) 未通过审核"
                if approval_reason:
                    content += f"\n\n审核意见：{approval_reason}"
                sendNotification(
                    None,
                    [obj.author],
                    content=content,
                    action_object=obj,
                    title="【通知】文章审核结果",
                )

                self.message_user(
                    request, f"文章 {obj.id} 已标记为不通过", messages.SUCCESS
                )
            return self._get_next_article_redirect(request, obj)

        return super().response_change(request, obj)

    def _get_next_article_redirect(self, request, current_obj):
        """Find the next unreviewed article and redirect to it."""
        # Find next unreviewed article (visibility=False)
        next_article = (
            Article.objects.filter(visibility=False, id__gt=current_obj.id)
            .order_by("id")
            .first()
        )

        if not next_article:
            # Try from the beginning if no article found after current
            next_article = (
                Article.objects.filter(visibility=False, id__lt=current_obj.id)
                .order_by("id")
                .first()
            )

        if next_article:
            # Redirect to the next unreviewed article
            return redirect(
                reverse("admin:article_article_change", args=[next_article.id])
            )
        else:
            # No more unreviewed articles, return to list
            self.message_user(request, "没有更多待审核的文章", messages.INFO)
            return redirect(reverse("admin:article_article_changelist"))

    def pass_visibility(self, request, queryset):
        updated = 0
        for article in queryset:
            was_visible = article.visibility
            article.visibility = True
            article.save()
            # Send notification only if the article was not previously visible
            if not was_visible:
                updated += 1
                sendNotification(
                    None,
                    [article.author],
                    content=f"恭喜您的文章(id={article.id}) 已通过审核",
                    action_object=article,
                    title="【通知】文章审核结果",
                )
        self.message_user(
            request,
            ngettext(
                "%d 篇文章被成功标记为可见。",
                "%d 篇文章被成功标记为可见。",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    pass_visibility.short_description = "所选 文章 通过审核"

    def withdraw_visibility(self, request, queryset):
        updated = 0
        for article in queryset:
            if article.visibility:
                article.visibility = False
                article.save()
                updated += 1
                # Send notification
                sendNotification(
                    None,
                    [article.author],
                    content=f"很遗憾，您的文章(id={article.id}) 未通过审核",
                    action_object=article,
                    title="【通知】文章审核结果",
                )
        self.message_user(
            request,
            ngettext(
                "%d 篇文章被成功标记为不可见。",
                "%d 篇文章被成功标记为不可见。",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    withdraw_visibility.short_description = "所选 文章 不通过审核"

    actions = ["pass_visibility", "withdraw_visibility"]


class CommentAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "article", "time"]
    list_filter = ["user", "article"]
    search_fields = ["user__username", "content", "article__title", "id"]
    date_hierarchy = "time"
    ordering = ["id", "-time"]
    list_per_page = 50
    raw_id_fields = ("parent", "article", "user")


admin.site.register(Article, ArticleAdmin)
admin.site.register(Comment, CommentAdmin)
