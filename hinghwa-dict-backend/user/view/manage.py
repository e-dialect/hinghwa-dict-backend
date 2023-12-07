import demjson
from django.db.models import Sum
from django.http import JsonResponse
from django.views import View
from notifications.models import Notification

from user.dto.user_all import user_all
from user.forms import UserForm, UserInfoForm
from user.utils import get_user_by_id
from utils.PasswordValidation import password_validator
from utils.Upload import uploadAvatar
from utils.exception.types.bad_request import BadRequestException
from utils.exception.types.forbidden import ForbiddenException
from utils.exception.types.unauthorized import WrongPassword
from utils.token import get_request_user, generate_token
from website.views import email_check
from utils.exception.types.not_found import UserNotFoundException
from user.models import UserInfo, User
from utils.token import token_pass, token_user


class Manage(View):
    # US0201 获取用户信息
    def get(self, request, id):
        user = get_user_by_id(id)

        # 创建默认用户信息
        if not hasattr(user, "user_info"):
            user.userinfo = UserInfo.objects.create(user=user, nickname=user.username)
            user.save()

        # 获取用户信息
        publish_articles = [
            article.get("id")
            for article in user.articles.all().order_by("-update_time").values("id")
        ]
        publish_comment = [
            comment.get("id")
            for comment in user.comments.all().order_by("-time").values("id")
        ]
        like_articles = [
            article.get("id")
            for article in user.like_articles.all()
            .order_by("-update_time")
            .values("id")
        ]

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
                "article_views": user.articles.aggregate(Sum("views"))["views__sum"]
                or 0,
                # TODO 去除播放量相关（需要确认前端全部删除）
                "listened": user.contribute_pronunciation.aggregate(Sum("views")).get(
                    "views__sum"
                )
                or 0,
            },
        }

        request_user = get_request_user(request)
        # 如果是本人额外返回邮件
        if request_user.id == id:
            sent = Notification.objects.filter(actor_object_id=id)
            received = Notification.objects.filter(recipient_id=id)
            unread = received.filter(unread=True)
            response.update(
                {
                    "notification": {
                        "statistics": {
                            "total": sent.count() + received.count(),
                            "sent": sent.count(),
                            "received": received.count(),
                            "unread": unread.count(),
                        },
                    }
                }
            )
        return JsonResponse(response, status=200)

    # US0301 修改用户信息
    def put(self, request, id):
        request_user = get_request_user(request)
        if request_user.id != id:
            raise ForbiddenException
        user = get_user_by_id(id)
        body = demjson.decode(request.body)
        info = body["user"]
        print(info)
        print(info["town"])
        print(info["county"])
        user_info_form = UserInfoForm(info)
        if not user_info_form.is_valid:
            raise ValueError
        # update fields
        for key in user_info_form.fields:
            setattr(user.user_info, key, body["user"][key])
        # special fields
        if "avatar" in info:
            user.user_info.avatar = uploadAvatar(user.id, info["avatar"])
        user.user_info.save()
        user.save()

        return JsonResponse(
            {
                "user": user_all(user),
                "token": generate_token(user),
            },
            status=200,
        )


class ManagePassword(View):
    # US0302 更新用户密码
    def put(self, request, id) -> JsonResponse:
        user = get_request_user(request)
        if user.id != id:
            raise ForbiddenException
        body = demjson.decode(request.body)
        if not user.check_password(body["oldpassword"]):
            raise WrongPassword()
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

    # US0307 微信更新用户密码
    def post(self, request, id) -> JsonResponse:
        user = get_request_user(request)
        if user.id != id:
            raise ForbiddenException
        body = demjson.decode(request.body)
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


class ManageEmail(View):
    # US0303 更新用户邮箱
    def put(self, request, id) -> JsonResponse:
        user = get_request_user(request)
        if user.id != id:
            raise ForbiddenException
        body = demjson.decode(request.body)
        if not email_check(body["email"], body["code"]):
            raise BadRequestException("验证码错误")
        user.email = body["email"]
        user.save()
        return JsonResponse({"user": user_all(user)}, status=200)


class ManagePoints(View):
    # US0204 获取用户积分信息
    def get(self, request, id) -> JsonResponse:
        user = get_user_by_id(id)
        points_sum = int(user_all(user)["points_sum"])
        points_now = int(user_all(user)["points_now"])
        return JsonResponse(
            {
                "points_sum": points_sum,
                "points_now": points_now,
            },
            status=200,
        )
