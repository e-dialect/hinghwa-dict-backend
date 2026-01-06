import demjson3
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
from utils.exception.types.forbidden import ForbiddenException
from utils.token import generate_token, check_request_user
from user.dto.user_all import user_all


class OpenId:
    def __init__(self, jscode):
        self.url = "https://api.weixin.qq.com/sns/jscode2session"
        self.app_id = settings.APP_ID
        self.app_secret = settings.APP_SECRECT
        self.jscode = jscode
        self.response_data = None

    def _fetch_data(self):
        """Fetch data from WeChat API if not already fetched"""
        if self.response_data is None:
            url = (
                f"{self.url}?appid={self.app_id}&secret={self.app_secret}&js_code={self.jscode}"
                f"&grant_type=authorization_code"
            )
            res = requests.get(url)
            data = res.json()
            if "errcode" in data:
                raise NotFoundException(
                    f"微信登录失败: {data.get('errmsg', '未知错误')}"
                )
            self.response_data = data

    def get_openid(self) -> str:
        self._fetch_data()
        return self.response_data["openid"].strip()

    def get_session_key(self) -> str:
        """Get session_key for decrypting phone number and other sensitive data"""
        self._fetch_data()
        return self.response_data.get("session_key", "")


class WechatLogin(View):
    # LG0102 微信登录
    def post(self, request):
        body = demjson3.decode(request.body)
        jscode = body["jscode"]
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
        body = demjson3.decode(request.body)
        user_form = UserFormByWechat(body)
        jscode = body["jscode"]
        #   获取微信信息
        openid = OpenId(jscode).get_openid()
        user_info = UserInfo.objects.filter(wechat__contains=openid)
        if user_info.exists():  # 微信号有记录了
            return JsonResponse({"msg": "该微信已绑定账户"}, status=409)
        if not user_form.is_valid():
            if user_form["username"].errors:
                return JsonResponse({"msg": "用户名重复"}, status=409)
            else:
                # Provide more detailed error information
                error_details = []
                for field, errors in user_form.errors.items():
                    error_details.append(f"{field}: {', '.join(errors)}")
                return JsonResponse(
                    {"msg": "表单验证失败", "errors": error_details}, status=400
                )
        else:
            user = user_form.save(commit=False)
            password_validator(user_form.cleaned_data["password"])
            user.set_password(user_form.cleaned_data["password"])
            # Set empty email for WeChat-only registration
            if not user.email:
                user.email = ""
            # Save user first before creating UserInfo
            user.save()

            # Now create UserInfo with saved user
            user_info = UserInfo.objects.create(user=user, nickname=user.username)
            user_info.wechat = openid
            if "nickname" in body:
                user_info.nickname = body["nickname"]
            if "avatar" in body:
                user_info.avatar = uploadAvatar(user.id, body["avatar"], suffix="png")
            # Add phone number if provided
            if "telephone" in body:
                user_info.telephone = body["telephone"]
            user_info.save()
            return JsonResponse(
                {"id": user.id, "token": generate_token(user)}, status=200
            )


class BindWechat(View):
    # US0304 绑定微信
    def put(self, request, id) -> JsonResponse:
        user = check_request_user(request, id)
        body = demjson3.decode(request.body)
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


class WechatManage(View):
    # US0307 微信更新用户密码
    def post(self, request, id) -> JsonResponse:
        #    基于token获取的用户
        user = check_request_user(request, id)
        if user.id != id:
            raise ForbiddenException
        body = demjson3.decode(request.body)
        jscode = body["jscode"]
        openid = OpenId(jscode).get_openid()
        #   基于jscode获取的用户
        user_info = UserInfo.objects.filter(wechat__contains=openid)
        if user_info[0].user != user:
            raise ForbiddenException
        password_validator(body["newpassword"])
        user.set_password(body["newpassword"])
        user.save()
        return JsonResponse(
            {
                "user": user_all(user),
                "token": generate_token(user),
            },
            status=200,
        )


class WechatWebAuth:
    """Handle Web/H5 WeChat OAuth authentication"""

    def __init__(self, code):
        self.code = code
        self.app_id = (
            settings.WEB_APP_ID if hasattr(settings, "WEB_APP_ID") else settings.APP_ID
        )
        self.app_secret = (
            settings.WEB_APP_SECRET
            if hasattr(settings, "WEB_APP_SECRET")
            else settings.APP_SECRECT
        )
        self.response_data = None

    def _fetch_access_token(self):
        """Fetch access token from WeChat Web OAuth API"""
        if self.response_data is None:
            url = (
                f"https://api.weixin.qq.com/sns/oauth2/access_token"
                f"?appid={self.app_id}&secret={self.app_secret}"
                f"&code={self.code}&grant_type=authorization_code"
            )
            res = requests.get(url)
            data = res.json()
            if "errcode" in data:
                raise NotFoundException(
                    f"微信网页授权失败: {data.get('errmsg', '未知错误')}"
                )
            self.response_data = data

    def get_openid(self) -> str:
        """Get user's openid from WeChat Web OAuth"""
        self._fetch_access_token()
        return self.response_data["openid"].strip()

    def get_user_info(self) -> dict:
        """Get user info including nickname, avatar, etc."""
        self._fetch_access_token()
        access_token = self.response_data["access_token"]
        openid = self.response_data["openid"]
        url = f"https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}&lang=zh_CN"
        res = requests.get(url)
        user_info = res.json()
        if "errcode" in user_info:
            raise NotFoundException(
                f"获取微信用户信息失败: {user_info.get('errmsg', '未知错误')}"
            )
        return user_info


class WechatWebLogin(View):
    """Web/H5 WeChat OAuth login"""

    def post(self, request):
        body = demjson3.decode(request.body)
        code = body["code"]
        wechat_auth = WechatWebAuth(code)
        openid = wechat_auth.get_openid()
        user_info = UserInfo.objects.filter(wechat__contains=openid)
        if not user_info.exists():
            raise NotFoundException("当前微信未绑定账号")
        user = user_info[0].user
        user.last_login = timezone.now()
        user.save()
        return JsonResponse({"token": generate_token(user), "id": user.id}, status=200)


class WechatWebRegister(View):
    """Web/H5 WeChat OAuth registration with one-click"""

    def post(self, request):
        body = demjson3.decode(request.body)
        code = body["code"]
        wechat_auth = WechatWebAuth(code)
        openid = wechat_auth.get_openid()

        # Check if WeChat already bound
        user_info = UserInfo.objects.filter(wechat__contains=openid)
        if user_info.exists():
            return JsonResponse({"msg": "该微信已绑定账户"}, status=409)

        # Get WeChat user info for nickname and avatar
        try:
            wechat_user_info = wechat_auth.get_user_info()
        except:
            wechat_user_info = {}

        # Validate required fields
        user_form = UserFormByWechat(body)
        if not user_form.is_valid():
            if user_form["username"].errors:
                return JsonResponse({"msg": "用户名重复"}, status=409)
            else:
                error_details = []
                for field, errors in user_form.errors.items():
                    error_details.append(f"{field}: {', '.join(errors)}")
                return JsonResponse(
                    {"msg": "表单验证失败", "errors": error_details}, status=400
                )

        # Create user
        user = user_form.save(commit=False)
        password_validator(user_form.cleaned_data["password"])
        user.set_password(user_form.cleaned_data["password"])
        if not user.email:
            user.email = ""

        # Save user first
        user.save()

        # Create user info with WeChat data
        nickname = (
            body.get("nickname") or wechat_user_info.get("nickname") or user.username
        )
        avatar = body.get("avatar") or wechat_user_info.get("headimgurl") or ""

        user_info = UserInfo.objects.create(user=user, nickname=nickname)
        user_info.wechat = openid

        if avatar:
            if avatar.startswith("http"):
                user_info.avatar = avatar
            else:
                user_info.avatar = uploadAvatar(user.id, avatar, suffix="png")

        if "telephone" in body:
            user_info.telephone = body["telephone"]

        user_info.save()
        return JsonResponse({"id": user.id, "token": generate_token(user)}, status=200)


class BindWechatWeb(View):
    """Bind Web/H5 WeChat OAuth to existing account"""

    def put(self, request, id) -> JsonResponse:
        user = check_request_user(request, id)
        body = demjson3.decode(request.body)
        code = body["code"]
        wechat_auth = WechatWebAuth(code)
        openid = wechat_auth.get_openid()

        if UserInfo.objects.filter(wechat=openid).exists():
            return JsonResponse({"msg": "该微信已绑定其他账号"}, status=409)
        if len(user.user_info.wechat):
            if not body.get("overwrite", False):
                return JsonResponse({"msg": "该账户已绑定微信"}, status=409)

        user.user_info.wechat = openid
        user.user_info.save()
        return JsonResponse({}, status=200)
