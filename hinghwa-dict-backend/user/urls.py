from django.urls import path

from .views import *

app_name = "users"

urlpatterns = [
    path("<int:id>", manageInfo),
    path("<int:id>/pronunciation", pronunciation),
    path("<int:id>/password", csrf_exempt(UpdatePassword.as_view())),  # US0302
    path("<int:id>/wechat", csrf_exempt(UpdateWechat.as_view())),  # US0304 US0305
    path("<int:id>/email", updateEmail),
    path("app", app),
    path("forget", forget),
    path("wechat", wxlogin),
    path("wechat/register", csrf_exempt(WechatOperation.as_view())),
]
