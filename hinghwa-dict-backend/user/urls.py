from django.urls import path

from .view.wechat import WechatLogin, WechatRegister, BindWechat
from .views import *
from .view.manage import *
from .view.forget import *

app_name = "users"

urlpatterns = [
    path("<int:id>/pronunciation", pronunciation),
    path("app", app),
    path("forget", csrf_exempt(Forget.as_view())),  # get LG0201 put LG0202
]

# 用户信息管理
urlpatterns += [
    path("<int:id>", csrf_exempt(Manage.as_view())),  # get US0201 put US0301
    path("<int:id>/password", csrf_exempt(ManagePassword.as_view())),  # put US0302
    path("<int:id>/password/reset", csrf_exempt(ManagePassword.as_view())),  # post US0307
    path("<int:id>/email", csrf_exempt(ManageEmail.as_view())),  # put US0303
    path("<int:id>/points", csrf_exempt(ManagePoints.as_view())),
]

# 微信相关操作
urlpatterns += [
    path("wechat", csrf_exempt(WechatLogin.as_view())),  # post LG0102
    path("wechat/register", csrf_exempt(WechatRegister.as_view())),  # post LG0103
    path(
        "<int:id>/wechat", csrf_exempt(BindWechat.as_view())
    ),  # put US0304 delete US0305
]
