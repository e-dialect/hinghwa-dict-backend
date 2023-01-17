from django.views import View
from user.forms import UserForm, UserInfoForm
from utils.Upload import uploadAvatar
from utils.exception.types.bad_request import BadRequestException
from utils.exception.types.forbidden import ForbiddenException
from utils.token import get_request_user
from user.models import UserInfo, User
from django.db.models import Sum
from user.utils import get_user_by_id
from user.dto.user_all import user_all
from user.dto.user_simple import user_simple
from notifications.models import Notification
from django.http import JsonResponse


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
            article.id
            for article in user.articles.all().values("id").order_by("-update_time")
        ]
        publish_comment = [
            comment.id for comment in user.comments.all().values("id").order_by("-time")
        ]
        like_articles = [
            article.id
            for article in user.like_articles.all()
            .values("id")
            .order_by("-update_time")
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
                # TODO 去除播放量相关（需要确认前端全部删除）
                "listened": user.contribute_pronunciation.aggregate(Sum("views"))[
                    "views__sum"
                ],
            },
        }

        request_user = get_request_user(request)
        # 如果是本人额外返回邮件 TODO 独立邮件接口
        if request_user.id == id:
            sent = [
                {
                    "id": note.id,
                    "from": user_simple(User.objects.get(id=note.actor_object_id)),
                    "to": user_simple(User.objects.get(id=note.recipient_id)),
                    "time": note.timestamp.__format__("%Y-%m-%d %H:%M:%S"),
                    "title": note.verb,
                }
                for note in Notification.objects.filter(actor_object_id=id).order_by(
                    "-timestamp"
                )
            ]
            received = Notification.objects.filter(recipient_id=id).order_by(
                "-timestamp"
            )
            unread = received.filter(unread=True)
            received = [
                {
                    "id": note.id,
                    "from": user_simple(User.objects.get(id=note.actor_object_id)),
                    "to": user_simple(User.objects.get(id=note.recipient_id)),
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

    # US0301 修改用户信息
    def put(self, request, id):
        request_user = get_request_user(request)
        if request_user.id != id:
            raise ForbiddenException
        user = get_user_by_id(id)
        try:
            info = request.POST["user"]
            user_form = UserForm(info)
            user_info_form = UserInfoForm(info)
            user_info_form.cleaned_data.pop("user")
            if not user_form.is_valid or not user_info_form.is_valid:
                raise ValueError
            # forbid to change username
            user_form.cleaned_data.pop("username")
            # update fileds
            for key, value in user_form.cleaned_data.items():
                setattr(user, key, value)
            for key, value in user_info_form.cleaned_data.items():
                setattr(user.user_info, key, value)
            # special fields
            if "avatar" in info:
                user.user_info.avatar = uploadAvatar(user.id, info["avatar"])
            user.user_info.save()
            user.save()

        except KeyError:
            raise BadRequestException("字段不合法")
        except ValueError:
            raise BadRequestException("值不合法")
        return JsonResponse({"user": user_all(user)}, status=200)
