# -*-coding:utf-8-*-
import os

import demjson3
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from notifications.models import Notification
from pydub import AudioSegment as audio

from article.models import Article
from word.models import Word, split
from .audio import split_ipa_from_mp3
from .forms import DailyExpressionForm
from .models import Website, DailyExpression
from .notification.dto import notification_normal
from .notification.utils import sendNotification, readNotification
from .storage import upload_file, delete_file
from user.dto.user_simple import user_simple
from .utils import (
    globalVar,
    email_check,
    token_check,
    random_str,
    filterInOrder,
)

# Import scheduler module to ensure background jobs are registered on startup
from . import scheduler  # noqa: F401


@csrf_exempt
@require_POST
def email(request):
    def check(email):
        return str(email).find("@") == -1

    try:
        body = demjson3.decode(request.body)
        email = body["email"].replace(" ", "")
        if check(email):
            return JsonResponse({}, status=400)
        else:
            code = random_str(digit_only=True)
            subject = "[兴化语记]验证码"
            msg = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
</head>
<body>
    <p><strong>亲爱的用户：</strong></p>
    <div style="margin-left: 20px"><p>你的验证码为：<strong>{0}</strong>(有效时间10分钟)</p></div>
    <p>兴化语记团队</p>
    <p>{1}</p>
</body>
</html>""".format(
                code, timezone.now().date()
            )
            send_mail(
                subject,
                "aaa",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[
                    email,
                ],
                html_message=msg,
            )
            globalVar.email_code[email] = (code, timezone.now())
            return JsonResponse({}, status=200)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def announcements(request):
    try:
        item = Website.objects.get(id=1)
        if request.method == "GET":
            articles = eval(item.announcements) if item.announcements else []
            result = Article.objects.filter(id__in=articles).filter(visibility=True)
            result = filterInOrder(result, articles)
            announcements = []
            for article in result:
                announcements.append(
                    {
                        "article": {
                            "id": article.id,
                            "likes": article.like_users.count(),
                            "author": article.author.id,
                            "views": article.views,
                            "publish_time": article.publish_time.__format__(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "update_time": article.update_time.__format__(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "title": article.title,
                            "description": article.description,
                            "content": article.content,
                            "cover": article.cover,
                            "visibility": article.visibility,
                        },
                        "author": user_simple(article.author),
                    }
                )
            return JsonResponse({"announcements": announcements}, status=200)
        elif request.method == "PUT":
            body = demjson3.decode(request.body)
            token = request.headers["token"]
            if token_check(token, settings.JWT_KEY, -1):
                if isinstance(body["announcements"], list):
                    item.announcements = body["announcements"]
                    item.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def hot_articles(request):
    try:
        item = Website.objects.get(id=1)
        if request.method == "GET":
            articles = eval(item.hot_articles) if item.hot_articles else []
            result = Article.objects.filter(id__in=articles).filter(visibility=True)
            result = filterInOrder(result, articles)
            hot_articles = []
            for article in result:
                hot_articles.append(
                    {
                        "article": {
                            "id": article.id,
                            "likes": article.like_users.count(),
                            "author": article.author.id,
                            "views": article.views,
                            "publish_time": article.publish_time.__format__(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "update_time": article.update_time.__format__(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "title": article.title,
                            "description": article.description,
                            "content": article.content,
                            "cover": article.cover,
                            "visibility": article.visibility,
                        },
                        "author": user_simple(article.author),
                    }
                )
            return JsonResponse({"hot_articles": hot_articles}, status=200)
        elif request.method == "PUT":
            body = demjson3.decode(request.body)
            token = request.headers["token"]
            if token_check(token, settings.JWT_KEY, -1):
                if isinstance(body["hot_articles"], list):
                    item.hot_articles = body["hot_articles"]
                    item.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def word_of_the_day(request):
    try:
        item = Website.objects.get(id=1)
        if request.method == "GET":
            word = Word.objects.get(id=item.word_of_the_day)
            return JsonResponse(
                {
                    "word_of_the_day": {
                        "id": word.id,
                        "word": word.word,
                        "definition": word.definition,
                        "contributor": word.contributor.id,
                        "annotation": word.annotation,
                        "mandarin": eval(word.mandarin) if word.mandarin else [],
                        "views": word.views,
                    }
                },
                status=200,
            )
        elif request.method == "PUT":
            body = demjson3.decode(request.body)
            token = request.headers["token"]
            if token_check(token, settings.JWT_KEY, -1):
                if isinstance(body["word_of_the_day"], int):
                    item.word_of_the_day = body["word_of_the_day"]
                    item.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def carousel(request):
    try:
        item = Website.objects.get(id=1)
        if request.method == "GET":
            return JsonResponse(
                {"carousel": eval(item.carousel) if item.carousel else []}, status=200
            )
        elif request.method == "PUT":
            body = demjson3.decode(request.body)
            token = request.headers["token"]
            if token_check(token, settings.JWT_KEY, -1):
                if isinstance(body["carousel"], list) and isinstance(
                    body["carousel"][0], dict
                ):
                    item.carousel = body["carousel"]
                    item.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def files(request):
    try:
        token = request.headers["token"]
        user = token_check(token, settings.JWT_KEY)
        if user:
            if request.method == "POST":
                file = request.FILES.get("file")
                type = str(file.content_type).split("/")[0]
                if file._name.find(".") != -1:
                    suffix = file._name.rsplit(".")[-1]
                elif type == "image":
                    suffix = "png"
                elif type == "video":
                    suffix = "mp4"
                else:
                    suffix = "mp3"
                time = timezone.now().__format__("%Y_%m_%d")
                filename = time + "_" + random_str(15) + "." + suffix
                folder = os.path.join(settings.MEDIA_ROOT, type, str(user.id))
                if not os.path.exists(folder):
                    os.makedirs(folder)
                path = os.path.join(folder, filename)
                if type != "audio":
                    with open(path, "wb") as f:
                        for i in file.chunks():
                            f.write(i)
                else:
                    music = audio.from_file(file)
                    music.set_frame_rate(44100)
                    music.export(path, format="mp3")
                key = (
                    "files/{}/{}/".format(type, user.id)
                    + timezone.now().__format__("%Y/%m/%d/")
                    + filename.split("_")[-1]
                )
                url = upload_file(path, key)
                return JsonResponse({"url": url}, status=200)
            elif request.method == "DELETE":
                body = demjson3.decode(request.body)
                try:
                    suffix = body["url"].split("/", 4)[-1]
                    type = suffix.split("/", 2)[0]
                    id = suffix.split("/", 2)[1]
                    if user.id == eval(id) or user.is_superuser:
                        filename = suffix.split("/", 2)[2]
                        filename = "_".join(filename.split("/"))
                        path = os.path.join(settings.MEDIA_ROOT, type, id, filename)
                        if os.path.exists(path):
                            os.remove(path)
                            key = body["url"].split("/", 3)[-1]
                            delete_file(key)
                            return JsonResponse({}, status=200)
                        else:
                            return JsonResponse({}, status=404)
                    else:
                        return JsonResponse({}, status=401)
                except Exception as e:
                    return JsonResponse({}, status=404)
        else:
            return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def openUrl(request, type, id, Y, M, D, X):
    try:
        filename = "{}_{}_{}_{}".format(Y, M, D, X)
        path = os.path.join(settings.MEDIA_ROOT, type, id, filename)
        if os.path.exists(path):
            with open(path.encode("utf-8"), "rb") as f:
                response = HttpResponse(
                    f.read(), content_type="application/octet-stream"
                )
                response["Content-Disposition"] = "attachment; filename={}".format(X)
                return response
        else:
            return JsonResponse({}, status=500)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def searchDailyExpression(request):
    try:
        if request.method == "GET":
            if "keyword" in request.GET:
                key = request.GET["keyword"]
                words = DailyExpression.objects.filter(
                    Q(english__icontains=key)
                    | Q(character__icontains=key)
                    | Q(pinyin__icontains=key)
                    | Q(mandarin__icontains=key)
                )
            else:
                words = DailyExpression.objects.all()
            pageSize = int(request.GET["pageSize"])
            page = int(request.GET["page"])
            r = min(len(words), page * pageSize)
            l = min(len(words) + 1, (page - 1) * pageSize)
            results = []
            for word in words[l:r]:
                results.append(
                    {
                        "key": word.id,
                        "english": word.english,
                        "mandarin": word.mandarin,
                        "character": word.character,
                        "pinyin": word.pinyin,
                    }
                )
            return JsonResponse(
                {
                    "results": results,
                    "total": {
                        "page": (len(words) - 1) // pageSize + 1,
                        "item": len(words),
                    },
                },
                status=200,
            )
        elif request.method == "POST":
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY, -1)
            if user:
                body = demjson3.decode(request.body)
                word_form = DailyExpressionForm(body)
                if word_form.is_valid():
                    word = word_form.save(commit=False)
                    word.save()
                    return JsonResponse(
                        {
                            "result": {
                                "key": word.id,
                                "english": word.english,
                                "mandarin": word.mandarin,
                                "character": word.character,
                                "pinyin": word.pinyin,
                            }
                        },
                        status=200,
                    )
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as msg:
        return JsonResponse({"msg": str(msg)}, status=500)


@csrf_exempt
def manageDailyExpression(request, id):
    try:
        token = request.headers["token"]
        user = token_check(token, settings.JWT_KEY, -1)
        if user:
            word = DailyExpression.objects.filter(id=id)
            if word.exists():
                word = word[0]
                if request.method == "PUT":
                    body = demjson3.decode(request.body)
                    for property in body["daily_expression"]:
                        setattr(word, property, body["daily_expression"][property])
                    word.save()
                    return JsonResponse(
                        {
                            "daily_expression": {
                                "key": word.id,
                                "english": word.english,
                                "mandarin": word.mandarin,
                                "character": word.character,
                                "pinyin": word.pinyin,
                            }
                        },
                        status=200,
                    )
                elif request.method == "DELETE":
                    word.delete()
                    return JsonResponse({}, status=204)
                else:
                    return JsonResponse({}, status=405)
            else:
                return JsonResponse({}, status=404)
        else:
            return JsonResponse({}, status=401)
    except Exception as msg:
        return JsonResponse({"msg": str(msg)}, status=500)


@csrf_exempt
def manageNotification(request, id):
    try:
        notification = Notification.objects.filter(id=id)
        if notification.exists():
            notification = notification[0]
            if request.method == "GET":
                token = request.headers["token"]
                user1 = token_check(
                    token, settings.JWT_KEY, notification.actor_object_id
                )
                user2 = token_check(token, settings.JWT_KEY, notification.recipient_id)
                if user1 or user2:
                    if user2 and user2.id == notification.recipient_id:
                        readNotification(notification)
                    return JsonResponse(notification_normal(notification), status=200)
                else:
                    return JsonResponse({}, status=401)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=404)
    except Exception as msg:
        return JsonResponse({"msg": str(msg)}, status=500)


@csrf_exempt
def manageNotificationUnread(request):
    try:
        token = request.headers["token"]
        user = token_check(token, settings.JWT_KEY)
        if user:
            if request.method == "PUT":
                body = demjson3.decode(request.body) if len(request.body) else {}
                notifications = Notification.objects.filter(recipient_id=user.id)
                if "notifications" in body:
                    notifications = notifications.filter(id__in=body["notifications"])
                for notification in notifications:
                    readNotification(notification)
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=401)
    except Exception as msg:
        return JsonResponse({"msg": str(msg)}, status=500)


@csrf_exempt
def test(request):
    try:
        folder = os.path.join(settings.BASE_DIR, "material", "audio", "老男单字")
        result = os.path.join(settings.BASE_DIR, "material", "audio", "result")
        name_ipas = os.path.join(settings.BASE_DIR, "material", "audio", "单字老男.csv")
        if not os.path.exists(result):
            os.mkdir(result)
        dic = {}
        with open(name_ipas, newline="", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                line = line.split(",")
                if len(line[2]) == 0:
                    continue
                name = line[1]
                ipas = split(line[2]).split()
                file = (line[0] if str.isdigit(line[0]) else "0001") + name + ".mp3"
                music = audio.from_file(os.path.join(folder, file))
                music.set_frame_rate(44100)
                start_ends = split_ipa_from_mp3(music, len(ipas))
                for ipa, (start, end) in zip(ipas, start_ends):
                    if ipa not in dic:
                        dic[ipa] = []
                    dic[ipa].append(music[start:end])
        sum = 0
        for i in dic.values():
            sum += len(i)
        for idx, (ipa, musics) in enumerate(dic.items()):
            path = os.path.join(result, ipa + ".mp3")
            musics[0].export(path, format="mp3")
            for i, music in zip(range(1, len(musics)), musics[1:]):
                path = os.path.join(result, ipa + f"-{i}.mp3")
                music.export(path, format="mp3")
        return JsonResponse({}, status=200)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)
