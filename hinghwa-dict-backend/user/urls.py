from django.urls import path

from .views import *
from user.view.manage import *

app_name = "users"

urlpatterns = [
    path("<int:id>/pronunciation", pronunciation),
    path("<int:id>/wechat", csrf_exempt(UpdateWechat.as_view())),  # US0304 US0305
    path("app", app),
    path("forget", forget),
    path("wechat", wxlogin),
    path("wechat/register", csrf_exempt(WechatOperation.as_view())),
]


# 用户信息管理
urlpatterns += [
    path("<int:id>", csrf_exempt(Manage.as_view())), # get US0201 put US0301
    path("<int:id>/password", csrf_exempt(ManagePassword.as_view())), # put US0302
    path("<int:id>/email", csrf_exempt(ManageEmail.as_view())), # put US0303
]
