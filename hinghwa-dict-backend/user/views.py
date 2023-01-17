import demjson
import requests
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from user.dto.user_all import user_all
from utils.PasswordValidation import password_validator
from django.views import View
from utils.exception.types.not_found import (
    UserNotFoundException,
    NotBoundWechat,
    NotBoundEmail,
)
from utils.token import generate_token, token_pass
from utils.Upload import uploadAvatar
from website.views import email_check, token_check
from word.pronunciation.dto.pronunciation_simple import pronunciation_simple
from .forms import UserForm, UserFormByWechat
from .models import UserInfo, User

# for '/users/'
@csrf_exempt
def router_users(request):
    try:
        # US0202 批量获取用户信息
        if request.method == "GET":
            result = User.objects.all()
            if "email" in request.GET:
                result = result.filter(email=request.GET["email"])
            if "username" in request.GET:
                result = result.filter(username=request.GET["username"])
            users = []
            for user in result:
                users.append(user_all(user))
            return JsonResponse({"users": users}, status=200)

        # US0101 新建用户
        elif request.method == "POST":
            body = demjson.decode(request.body)
            user_form = UserForm(body)
            code = body["code"]
            if user_form.is_valid():
                if email_check(user_form.cleaned_data["email"], code):
                    user = user_form.save(commit=False)
                    password_validator(user_form.cleaned_data["password"])
                    user.set_password(user_form.cleaned_data["password"])
                    user.save()
                    user_info = UserInfo.objects.create(
                        user=user, nickname=user.username
                    )
                    if "nickname" in body:
                        user_info.nickname = body["nickname"]
                    if "avatar" in body:
                        user_info.avatar = uploadAvatar(
                            user.id, body["avatar"], suffix="png"
                        )
                    user_info.save()
                    return JsonResponse({"id": user.id}, status=200)
                else:
                    return JsonResponse({}, status=401)
            else:
                if user_form["username"].errors:
                    return JsonResponse({}, status=409)
                else:
                    return JsonResponse({}, status=400)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def login(request):
    try:
        if request.method == "POST":
            body = demjson.decode(request.body)
            username = body["username"]
            password = body["password"]
            user = authenticate(username=username, password=password)
            if user:
                user.last_login = timezone.now()
                # 超级管理员初始状况下没有 userinfo 字段
                if not hasattr(user, "user_info"):
                    user.userinfo = UserInfo.objects.create(
                        user=user, nickname=user.username
                    )
                user.save()
                return JsonResponse(
                    {"token": generate_token(user), "id": user.id}, status=200
                )
            else:
                return JsonResponse({}, status=401)
        elif request.method == "PUT":
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY)
            if user:
                return JsonResponse(
                    {"token": generate_token(user), "id": user.id}, status=200
                )
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


class OpenId:
    def __init__(self, jscode):
        self.url = "https://api.weixin.qq.com/sns/jscode2session"
        self.app_id = settings.APP_ID
        self.app_secret = settings.APP_SECRECT
        self.jscode = jscode

    def get_openid(self) -> str:
        url = f"{self.url}?appid={self.app_id}&secret={self.app_secret}&js_code={self.jscode}&grant_type=authorization_code"
        res = requests.get(url)
        try:
            openid = res.json()["openid"]
            session_key = res.json()["session_key"]
        except KeyError:
            return "fail"
        else:
            return openid


@csrf_exempt
def wxlogin(request):
    try:
        body = demjson.decode(request.body)
        jscode = body["jscode"]
        openid = OpenId(jscode).get_openid().strip()
        user_info = UserInfo.objects.filter(wechat__contains=openid)
        if user_info.exists():
            user = user_info[0].user
            user.last_login = timezone.now()
            user.save()
            return JsonResponse(
                {"token": generate_token(user), "id": user.id}, status=200
            )
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


class WechatOperation(View):
    def post(self, request):
        body = demjson.decode(request.body)
        user_form = UserFormByWechat(body)
        jscode = body["jscode"]
        #   获取微信信息
        openid = OpenId(jscode).get_openid().strip()
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


@csrf_exempt
def pronunciation(request, id):
    try:
        user = User.objects.filter(id=id)
        if user.exists():
            user = user[0]
            if request.method == "GET":
                pronunciations = []
                for pronuncitaion in user.contribute_pronunciation.all():
                    pronunciations.append(pronunciation_simple(pronuncitaion))
                return JsonResponse({"pronunciation": pronunciations}, status=200)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def updateEmail(request, id):
    try:
        user = User.objects.filter(id=id)
        if user.exists():
            user = user[0]
            if request.method == "PUT":
                body = demjson.decode(request.body)
                token = request.headers["token"]
                if token_check(token, settings.JWT_KEY, id) and email_check(
                    body["email"], body["code"]
                ):
                    user.email = body["email"]
                    user.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


class UpdateWechat(View):
    def put(self, request, id) -> JsonResponse:
        user = User.objects.filter(id=id)
        if not user.exists():
            raise UserNotFoundException(id)
        user = user[0]
        body = demjson.decode(request.body)
        token_pass(request.headers, id)
        jscode = body["jscode"]
        openid = OpenId(jscode).get_openid().strip()
        if UserInfo.objects.filter(wechat=openid).exists():
            return JsonResponse({"msg": "该微信已绑定其他账号"}, status=409)
        if len(user.user_info.wechat):
            if not body["overwrite"]:
                return JsonResponse({"msg": "该账户已绑定微信"}, status=409)
        user.user_info.wechat = openid
        user.user_info.save()
        return JsonResponse({}, status=200)

    def delete(self, request, id) -> JsonResponse:
        user = User.objects.filter(id=id)
        if not user.exists():
            raise UserNotFoundException(id)
        user = user[0]
        token_pass(request.headers, id)
        if not len(user.user_info.wechat):
            raise NotBoundWechat(user.user_info.nickname)
        if not len(user.email):
            return JsonResponse({"msg": "未绑定邮箱，无法解绑微信"}, status=400)
        user.user_info.wechat = ""
        user.user_info.save()
        return JsonResponse({}, status=200)


# TODO 先暂时假定QQ操作完全同微信
@csrf_exempt
def updateQQ(request, id):
    try:
        user = User.objects.filter(id=id)
        if user.exists():
            user = user[0]
            if request.method == "PUT":
                token = request.headers["token"]
                body = demjson.decode(request.body)
                if token_check(token, settings.JWT_KEY, id):
                    jscode = body["jscode"]
                    openid = OpenId(jscode).get_openid().strip()
                    if not UserInfo.objects.filter(qq=openid).exists():
                        user.user_info.qq = openid
                        user.user_info.save()
                        return JsonResponse({}, status=200)
                    else:
                        return JsonResponse({}, status=409)
                else:
                    return JsonResponse({}, status=401)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def app(request):
    pass


@csrf_exempt
def forget(request):
    try:
        if request.method == "GET":
            # 返回用户邮箱
            user = User.objects.filter(username=request.GET["username"])
            if user.exists():
                user = user[0]
                email = user.email
                if email:
                    return JsonResponse({"email": email}, status=200)
                else:
                    raise NotBoundEmail(user.user_info.nickname)
            else:
                return JsonResponse({}, status=404)
        elif request.method == "PUT":
            # 检查验证码并重置用户密码
            body = demjson.decode(request.body)
            user = User.objects.filter(username=body["username"])
            if body["password"]:
                if user.exists():
                    user = user[0]
                    email = body["email"]
                    if user.email == email and email_check(email, body["code"]):
                        password_validator(body["password"])
                        user.set_password(body["password"])
                        user.save()
                        return JsonResponse({}, status=200)
                    else:
                        return JsonResponse({}, status=401)
                else:
                    return JsonResponse({}, status=404)
            else:
                return JsonResponse({}, status=400)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)
