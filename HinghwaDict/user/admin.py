from django.contrib import admin
from django.contrib.auth.models import Group

from .models import UserInfo


class UserInfoAdmin(admin.ModelAdmin):
    list_display = ['ID', 'user', 'nickname', 'telephone']
    search_fields = ['user', 'nickname', 'telephone', 'email', 'user__email']
    ordering = ['user__id']
    list_per_page = 50


admin.site.register(UserInfo, UserInfoAdmin)
admin.site.unregister(Group)
admin.site.site_url = "http://api.pxm.edialect.top"
admin.site.site_header = '兴化语记后台管理'
admin.site.site_title = "兴化语记后台管理"


