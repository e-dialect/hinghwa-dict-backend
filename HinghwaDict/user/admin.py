from django.contrib import admin
from django.contrib.auth.models import Group
from .models import UserInfo


class UserInfoAdmin(admin.ModelAdmin):
    list_display = ['ID', 'user', 'nickname', 'telephone']
    search_fields = ['user', 'nickname', 'telephone', 'email', 'user__email']

admin.site.register(UserInfo, UserInfoAdmin)
admin.site.unregister(Group)
