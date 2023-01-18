import demjson
import requests
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views import View

from user.forms import UserFormByWechat
from user.models import UserInfo
from utils.PasswordValidation import password_validator
from utils.Upload import uploadAvatar
from utils.exception.types.not_found import (
    NotBoundWechat,
    NotFoundException,
)
from utils.token import generate_token, check_request_user


class OpenId:
    def __init__(self, jscode):
        self.url = "https://api.weixin.qq.com/sns/jscode2session"
        self.app_id = settings.APP_ID
        self.app_secret = settings.APP_SECRECT
        self.jscode = jscode

    def get_openid(self) -> str:
        url = f"{self.url}?appid={self.app_id}&secret={self.app_secret}&js_code={self.jscode}&grant_type=authorization_code"
        res = requests.get(url)
        openid = res.json()["openid"]
        # session_key = res.json()["session_key"]
        return openid.strip()


class WechatLogin(View):
    # LG0102 微信登录
    def post(self, request):
        jscode = request.POST["jscode"]
        openid = OpenId(jscode).get_openid()
        user_info = UserInfo.objects.filter(wechat__contains=openid)
        if not user_info.exists():
            raise NotFoundException("当前微信未绑定账号")
        user = user_info[0].user
        user.last_login = timezone.now()
        user.save()
        return JsonResponse({"token": generate_token(user), "id": user.id}, status=200)


class WechatRegister(View):
    # US0102 新建用户（微信）
    def post(self, request):
        body = demjson.decode(request.body)
        user_form = UserFormByWechat(body)
        jscode = body["jscode"]
        #   获取微信信息
        openid = OpenId(jscode).get_openid()
        user_info = UserInfo.objects.filter(wechat__contains=openid)
        if user_info.exists():  # 微信号有记录了
            return JsonResponse({"msg": "该微信已绑定账户"}, status=409)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            password_validator(user_form.cleaned_data["password"])
            user.set_password(user_form.cleaned_data["password"])
            user.save()
            user_info = UserInfo.objects.create(user=user, nickname=user.username)
            user_info.wechat = openid
            if "nickname" in body:
                user_info.nickname = body["nickname"]
            if "avatar" in body:
                user_info.avatar = uploadAvatar(user.id, body["avatar"], suffix="png")
            user_info.save()
            return JsonResponse({}, status=200)
        else:
            if user_form["username"].errors:
                return JsonResponse({"msg": "用户名重复"}, status=409)
            else:
                return JsonResponse({"msg": "请求有误"}, status=400)


class BindWechat(View):
    # US0304 绑定微信
    def put(self, request, id) -> JsonResponse:
        user = check_request_user(request, id)
        body = demjson.decode(request.body)
        jscode = body["jscode"]
        openid = OpenId(jscode).get_openid()
        if UserInfo.objects.filter(wechat=openid).exists():
            return JsonResponse({"msg": "该微信已绑定其他账号"}, status=409)
        if len(user.user_info.wechat):
            if not body["overwrite"]:
                return JsonResponse({"msg": "该账户已绑定微信"}, status=409)
        user.user_info.wechat = openid
        user.user_info.save()
        return JsonResponse({}, status=200)

    # US0305 取消绑定微信
    def delete(self, request, id) -> JsonResponse:
        user = check_request_user(request, id)
        if not len(user.user_info.wechat):
            raise NotBoundWechat(user.user_info.nickname)
        if not len(user.email):
            return JsonResponse({"msg": "未绑定邮箱，无法解绑微信"}, status=403)
        user.user_info.wechat = ""
        user.user_info.save()
        return JsonResponse({}, status=200)
