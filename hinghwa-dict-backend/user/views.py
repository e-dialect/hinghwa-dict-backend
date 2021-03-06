import datetime
import os.path

import demjson
import jwt
import requests
from django.conf import settings
from django.contrib.auth import authenticate
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from notifications.models import Notification
from user.dto.user_all import user_all

from website.views import (
    random_str,
    email_check,
    token_check,
    download_file,
    simpleUserInfo,
)
from word.dto.pronunciation.pronunciation_simple import pronunciation_simple
from .forms import UserForm, UserInfoForm
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
                    user.set_password(user_form.cleaned_data["password"])
                    user.save()
                    user_info = UserInfo.objects.create(
                        user=user, nickname="用户{}".format(random_str())
                    )
                    if "avatar" in body:
                        # 下载连接中图片
                        suffix = "png"
                        time = timezone.now().__format__("%Y_%m_%d")
                        filename = time + "_" + random_str(15) + "." + suffix
                        url = download_file(
                            body["avatar"], "download", str(user.id), filename
                        )
                        if url is not None:
                            user_info.avatar = url
                    if "nickname" in body:
                        user_info.nickname = body["nickname"]
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
                user.save()
                payload = {
                    "username": username,
                    "id": user.id,
                    "exp": (
                        timezone.now() + datetime.timedelta(seconds=3600)
                    ).timestamp(),
                }
                # 不知道为什么，本地显示jwt.encode是Object但是服务器显示是str
                token = jwt.encode(payload, settings.JWT_KEY, algorithm="HS256")
                try:
                    token = token.decode("utf-8")
                except Exception as e:
                    pass
                return JsonResponse({"token": token, "id": user.id}, status=200)
            else:
                return JsonResponse({}, status=401)
        elif request.method == "PUT":
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY)
            if user:
                payload = {
                    "username": user.username,
                    "id": user.id,
                    "exp": (
                        timezone.now() + datetime.timedelta(seconds=3600)
                    ).timestamp(),
                }
                # 不知道为什么，本地显示jwt.encode是Object但是服务器显示是str
                token = jwt.encode(payload, settings.JWT_KEY, algorithm="HS256")
                try:
                    token = token.decode("utf-8")
                except Exception as e:
                    pass
                return JsonResponse({"token": token, "id": user.id}, status=200)
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
            payload = {
                "username": user.username,
                "id": user.id,
                "exp": (timezone.now() + datetime.timedelta(seconds=3600)).timestamp(),
            }
            token = jwt.encode(payload, settings.JWT_KEY, algorithm="HS256")
            try:
                token = token.decode("utf-8")
            except Exception as e:
                pass
            return JsonResponse({"token": token, "id": user.id}, status=200)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def manageInfo(request, id):
    try:
        user = User.objects.filter(id=id)
        if user.exists():
            user = user[0]
            if request.method == "GET":
                # 超级管理员初始状况下没有 userinfo 字段
                if not hasattr(user, "user_info"):
                    user.userinfo = UserInfo.objects.create(
                        user=user, nickname="用户{}".format(random_str())
                    )
                    user.save()

                # 获取用户信息
                publish_articles = [article.id for article in user.articles.all()]
                publish_comment = [comment.id for comment in user.comments.all()]
                like_articles = [article.id for article in user.like_articles.all()]
                contribute_listened = user.contribute_pronunciation.aggregate(
                    Sum("views")
                )["views__sum"]
                response = {
                    "user": user_all(user),
                    "publish_articles": publish_articles,
                    "publish_comments": publish_comment,
                    "like_articles": like_articles,
                    "contribution": {
                        "pronunciation": user.contribute_pronunciation.filter(
                            visibility=True
                        ).count(),
                        "pronunciation_uploaded": user.contribute_pronunciation.count(),
                        "word": user.contribute_words.filter(visibility=True).count(),
                        "word_uploaded": user.contribute_words.count(),
                        "listened": contribute_listened if contribute_listened else 0,
                    },
                }
                if "token" in request.headers:
                    token = request.headers["token"]
                    if token_check(token, settings.JWT_KEY, id):
                        sent = [
                            {
                                "id": note.id,
                                "from": simpleUserInfo(
                                    User.objects.get(id=note.actor_object_id)
                                ),
                                "to": simpleUserInfo(
                                    User.objects.get(id=note.recipient_id)
                                ),
                                "time": note.timestamp.__format__("%Y-%m-%d %H:%M:%S"),
                                "title": note.verb,
                            }
                            for note in Notification.objects.filter(
                                actor_object_id=id
                            ).order_by("-id")
                        ]
                        received = Notification.objects.filter(
                            recipient_id=id
                        ).order_by("-id")
                        unread = received.filter(unread=True)
                        received = [
                            {
                                "id": note.id,
                                "from": simpleUserInfo(
                                    User.objects.get(id=note.actor_object_id)
                                ),
                                "to": simpleUserInfo(
                                    User.objects.get(id=note.recipient_id)
                                ),
                                "time": note.timestamp.__format__("%Y-%m-%d %H:%M:%S"),
                                "title": note.verb,
                                "unread": note.unread,
                            }
                            for note in received
                        ]
                        response.update(
                            {
                                "notification": {
                                    "statistics": {
                                        "total": len(sent) + len(received),
                                        "sent": len(sent),
                                        "received": len(received),
                                        "unread": unread.count(),
                                    },
                                    "sent": sent,
                                    "received": received,
                                }
                            }
                        )

                return JsonResponse(response, status=200)
            elif request.method == "PUT":
                # 更新用户信息
                body = demjson.decode(request.body)
                token = request.headers["token"]
                if token_check(token, settings.JWT_KEY, id):
                    info = body["user"]
                    user_form = UserForm(info)
                    user_info_form = UserInfoForm(info)
                    if (
                        not (
                            ("username" in info)
                            and len(user_form["username"].errors.data)
                            and info["username"] != user.username
                        )
                        and user_info_form.is_valid()
                    ):
                        if "username" in info:
                            user.username = info["username"]
                        for key in info:
                            if key != "username":
                                setattr(user.user_info, key, info[key])
                        if ("avatar" in info) and info["avatar"].split("/", 3)[
                            2
                        ] not in ["api.pxm.edialect.top", "cos.edialect.top"]:
                            suffix = "png"
                            time = timezone.now().__format__("%Y_%m_%d")
                            filename = time + "_" + random_str(15) + "." + suffix
                            url = download_file(
                                info["avatar"], "download", str(user.id), filename
                            )
                            if url is not None:
                                user.user_info.avatar = url
                        user.save()
                        user.user_info.save()
                        payload = {
                            "username": user.username,
                            "id": user.id,
                            "exp": (
                                timezone.now() + datetime.timedelta(seconds=3600)
                            ).timestamp(),
                        }
                        token = jwt.encode(payload, settings.JWT_KEY, algorithm="HS256")
                        try:
                            token = token.decode("utf-8")
                        except Exception as e:
                            pass
                        return JsonResponse({"token": token}, status=200)
                    else:
                        if (
                            not user_form.is_valid()
                        ) and "username" in user_form.errors:
                            return JsonResponse({}, status=409)
                        else:
                            return JsonResponse({}, status=400)
                else:
                    return JsonResponse({}, status=401)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


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
def updatePassword(request, id):
    try:
        user = User.objects.filter(id=id)
        if user.exists():
            user = user[0]
            if request.method == "PUT":
                token = request.headers["token"]
                body = demjson.decode(request.body)
                if token_check(token, settings.JWT_KEY, id):
                    if user.check_password(body["oldpassword"]):
                        if body["newpassword"]:
                            user.set_password(body["newpassword"])
                            user.save()
                            return JsonResponse({}, status=200)
                        else:
                            return JsonResponse({}, status=400)
                    else:
                        return JsonResponse({}, status=401)
                else:
                    return JsonResponse({}, status=401)
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


@csrf_exempt
def updateWechat(request, id):
    try:
        user = User.objects.filter(id=id)
        if user.exists():
            user = user[0]
            token = request.headers["token"]
            body = demjson.decode(request.body)
            if request.method == "PUT":
                if token_check(token, settings.JWT_KEY, id):
                    jscode = body["jscode"]
                    openid = OpenId(jscode).get_openid().strip()
                    if not UserInfo.objects.filter(wechat=openid).exists():
                        user.user_info.wechat = openid
                        user.user_info.save()
                        return JsonResponse({}, status=200)
                    else:
                        return JsonResponse({}, status=409)
                else:
                    return JsonResponse({}, status=401)
            elif request.method == "DELETE":
                if token_check(token, settings.JWT_KEY, id) and len(
                    user.user_info.wechat
                ):
                    user.user_info.wechat = ""
                    user.user_info.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


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
                return JsonResponse({"email": user[0].email}, status=200)
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
