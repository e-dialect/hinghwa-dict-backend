import os
import random

import demjson
import jwt
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Website


class globalVar():
    email_code = {}


def email_check(email, code):
    email = str(email)
    if (email in globalVar.email_code) and \
            globalVar.email_code[email][0] == code and \
            globalVar.email_code[email][1] < timezone.now():
        globalVar.email_code.pop(email)
        return 1
    else:
        return 0


def token_check(token, key, id=0):
    try:
        info = jwt.decode(token, key, algorithms=['HS256'])
        user = User.objects.get(id=info['id'])
        if user.username == info['username'] and (id == 0 or id == info['id'] or user.is_superuser):
            return user
        else:
            return 0
    except:
        return 0


def random_str(n=6):
    _str = '1234567890abcdefghijklmnopqrstuvwxyz'
    return ''.join(random.choice(_str) for i in range(n))


@csrf_exempt
@require_POST
def email(request):
    def check(email):
        return str(email).find('@') == -1

    try:
        body = demjson.decode(request.body)
        email = body['email'].replace(' ', '')
        if check(email):
            return JsonResponse({}, status=400)
        else:
            code = random_str()
            subject = '[兴化语记]验证码'
            msg = '''<!DOCTYPE html>
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
</html>'''.format(code, timezone.now().date())
            send_mail(subject, 'aaa', from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[email, ],
                      html_message=msg)
            globalVar.email_code[email] = (code, timezone.now())
            return JsonResponse({}, status=200)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def announcements(request):
    body = demjson.decode(request.body)
    try:
        item = Website.objects.get(id=1)
        if request.method == 'GET':
            return JsonResponse({"announcements": item.announcements}, status=200)
        elif request.method == "PUT":
            token = request.headers['token']
            if token_check(token, 'dxw', -1):
                item.announcements = body["announcements"]
                item.save()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def hot_articles(request):
    body = demjson.decode(request.body)
    try:
        item = Website.objects.get(id=1)
        if request.method == 'GET':
            return JsonResponse({"hot_articles": item.hot_articles}, status=200)
        elif request.method == "PUT":
            token = request.headers['token']
            if token_check(token, 'dxw', -1):
                item.hot_articles = body["hot_articles"]
                item.save()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def word_of_the_day(request):
    body = demjson.decode(request.body)
    try:
        item = Website.objects.get(id=1)
        if request.method == 'GET':
            return JsonResponse({"word_of_the_day": item.word_of_the_day}, status=200)
        elif request.method == "PUT":
            token = request.headers['token']
            if token_check(token, 'dxw', -1):
                item.word_of_the_day = body["word_of_the_day"]
                item.save()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def carousal(request):
    body = demjson.decode(request.body)
    try:
        item = Website.objects.get(id=1)
        if request.method == 'GET':
            return JsonResponse({"carousal": item.carousal}, status=200)
        elif request.method == "PUT":
            token = request.headers['token']
            if token_check(token, 'dxw', -1):
                item.carousal = body["carousal"]
                item.save()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)





@csrf_exempt
def files(request):
    try:
        token = request.headers['token']
        user = token_check(token, 'dxw')
        if user:
            if request.method == "POST":
                file = request.FILES.get("file")
                type, suffix = str(file.content_type).split('/')
                time = timezone.now().__format__("%Y_%m_%d_%H_%M_%S")
                filename = time + '.' + suffix
                folder = os.path.join(settings.MEDIA_ROOT, type, str(user.id))
                if not os.path.exists(folder):
                    os.mkdir(folder)
                path = os.path.join(folder, filename)
                with open(path, 'wb') as f:
                    for i in file.chunks():
                        f.write(i)
                payload = {"id": user.id, "type": type, "filename": filename}
                url = 'http://api.pxm.edialect.top/files/' + jwt.encode(payload, "dxw", algorithm="HS256")
                return JsonResponse({"url": url}, status=200)
            elif request.method == 'DELETE':
                body = demjson.decode(request.body)
                info = jwt.decode(body['url'].split('/')[-1], "dxw", algorithms=["HS256"])
                if user.id == info['id']:
                    filename = info['filename']
                    path = os.path.join(settings.MEDIA_ROOT, info['type'], str(info['id']), filename)
                    if os.path.exists(path):
                        os.remove(path)
                        return JsonResponse({}, status=200)
                    else:
                        return JsonResponse({"msg": "文件不存在"}, status=500)
                else:
                    return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def openUrl(request, token):
    try:
        info = jwt.decode(token, "dxw", algorithms=["HS256"])
        filename = info['filename']
        path = os.path.join(settings.MEDIA_ROOT, info['type'], str(info['id']), filename)
        if os.path.exists(path):
            with open(path.encode('utf-8'), 'rb') as f:
                response = HttpResponse(f.read(), content_type="application/octet-stream")
                response['Content-Disposition'] = 'attachment; filename={0}'.format(path)
                return response
        else:
            return JsonResponse({}, status=500)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


if Website.objects.count() == 0:
    Website.objects.create()
