from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django import forms

from .models import UserInfo
from utils.admin.widgets import ImagePreviewWidget


class UserInfoAdminForm(forms.ModelForm):
    """Custom form for UserInfo admin with image preview for avatar."""

    class Meta:
        model = UserInfo
        fields = "__all__"
        widgets = {
            "avatar": ImagePreviewWidget(max_width=200, max_height=200),
        }


class UserInfoAdmin(admin.ModelAdmin):
    form = UserInfoAdminForm
    list_display = ["ID", "user", "nickname", "telephone"]
    search_fields = ["user__username", "nickname", "telephone", "user__email", "id"]
    ordering = ["user__id"]
    list_per_page = 50


admin.site.register(UserInfo, UserInfoAdmin)
admin.site.unregister(Group)
admin.site.site_url = "http://api.pxm.edialect.top"
admin.site.site_header = "兴化语记后台管理"
admin.site.site_title = "兴化语记后台管理"
UserAdmin.list_display = ("id", "username", "email", "is_staff", "is_superuser")
UserAdmin.ordering = ("id",)
