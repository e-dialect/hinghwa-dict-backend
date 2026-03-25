from django.urls import path

from .view.wechat import (
    WechatLogin,
    WechatRegister,
    BindWechat,
    WechatManage,
    WechatWebLogin,
    WechatWebRegister,
    BindWechatWeb,
)
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
    path("<int:id>/password/reset", csrf_exempt(WechatManage.as_view())),  # post US0307
    path(
        "<int:id>/email", csrf_exempt(ManageEmail.as_view())
    ),  # put US0303 delete US0306
    path("<int:id>/points", csrf_exempt(ManagePoints.as_view())),
]

# 微信相关操作 - 小程序
urlpatterns += [
    path("wechat", csrf_exempt(WechatLogin.as_view())),  # post LG0102
    path("wechat/register", csrf_exempt(WechatRegister.as_view())),  # post LG0103
    path(
        "<int:id>/wechat", csrf_exempt(BindWechat.as_view())
    ),  # put US0304 delete US0305
]

# 微信相关操作 - 网页版
urlpatterns += [
    path(
        "wechat/web", csrf_exempt(WechatWebLogin.as_view())
    ),  # post LG0104 网页微信登录
    path(
        "wechat/web/register", csrf_exempt(WechatWebRegister.as_view())
    ),  # post LG0105 网页微信注册
    path(
        "<int:id>/wechat/web", csrf_exempt(BindWechatWeb.as_view())
    ),  # put US0308 网页微信绑定
]
