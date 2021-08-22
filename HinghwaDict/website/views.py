import math
import os
import random

import demjson
import jwt
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_apscheduler.jobstores import DjangoJobStore, register_job, register_events
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

from article.models import Article
from word.models import Word
from .models import Website


class globalVar():
    email_code = {}


def email_check(email, code):
    email = str(email)
    if (email in globalVar.email_code) and \
            globalVar.email_code[email][0] == code and \
            (timezone.now() - globalVar.email_code[email][1]).seconds < 600:
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


def compare(item, key):
    total = 0
    j = 0
    m = len(key)
    for character in item:
        if character == key[j]:
            if j == m - 1:
                j = 0
                total += 1
            else:
                j += 1
        elif j:
            total += math.exp(j - m)
            j = 1 if character == key[0] else 0
    if j:
        total += math.exp(j - m)
    return total


def evaluate(standard, key):
    total = 0
    key = str(key)
    for item, score in standard:
        item = str(item)
        if len(item) > 0:
            total += (compare(item, key) + compare(item[::-1], key[::-1])) * score / math.log(3 + len(item))
    return total


def random_str(n=6):
    _str = '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
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
    try:
        item = Website.objects.get(id=1)
        if request.method == 'GET':
            articles = eval(item.announcements) if item.announcements else []
            articles = Article.objects.filter(id__in=articles)
            announcements = []
            for article in articles:
                announcements.append({
                    'article': {"id": article.id, "likes": article.like_users.count(), 'author': article.author.id,
                                "views": article.views,
                                "publish_time": article.publish_time.__format__('%Y-%m-%d %H:%M:%S'),
                                "update_time": article.update_time.__format__('%Y-%m-%d %H:%M:%S'),
                                "title": article.title, "description": article.description, "content": article.content,
                                "cover": article.cover},
                    'author': {'id': article.author.id, 'nickname': article.author.user_info.nickname,
                               'avatar': article.author.user_info.avatar}})
            return JsonResponse({"announcements": announcements}, status=200)
        elif request.method == "PUT":
            body = demjson.decode(request.body)
            token = request.headers['token']
            if token_check(token, '***REMOVED***', -1):
                if isinstance(body['announcements'],list):
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
        if request.method == 'GET':
            articles = eval(item.hot_articles) if item.hot_articles else []
            articles = Article.objects.filter(id__in=articles)
            hot_articles = []
            for article in articles:
                hot_articles.append({
                    'article': {"id": article.id, "likes": article.like_users.count(), 'author': article.author.id,
                                "views": article.views,
                                "publish_time": article.publish_time.__format__('%Y-%m-%d %H:%M:%S'),
                                "update_time": article.update_time.__format__('%Y-%m-%d %H:%M:%S'),
                                "title": article.title, "description": article.description, "content": article.content,
                                "cover": article.cover},
                    'author': {'id': article.author.id, 'nickname': article.author.user_info.nickname,
                               'avatar': article.author.user_info.avatar}})
            return JsonResponse({"hot_articles": hot_articles}, status=200)
        elif request.method == "PUT":
            body = demjson.decode(request.body)
            token = request.headers['token']
            if token_check(token, '***REMOVED***', -1):
                if isinstance(body['hot_articles'], list):
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
        if request.method == 'GET':
            word = Word.objects.get(id=item.word_of_the_day)
            return JsonResponse({"word_of_the_day": {"id": word.id, 'word': word.word, 'definition': word.definition,
                                                     "contributor": word.contributor.id, "annotation": word.annotation,
                                                     "mandarin": eval(word.mandarin) if word.mandarin else [],
                                                     "views": word.views}}, status=200)
        elif request.method == "PUT":
            body = demjson.decode(request.body)
            token = request.headers['token']
            if token_check(token, '***REMOVED***', -1):
                if isinstance(body['word_of_the_day'], int):
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
        if request.method == 'GET':
            return JsonResponse({"carousel": eval(item.carousel) if item.carousel else []}, status=200)
        elif request.method == "PUT":
            body = demjson.decode(request.body)
            token = request.headers['token']
            if token_check(token, '***REMOVED***', -1):
                if isinstance(body['carousel'], list) and isinstance(body['carousel'][0], dict):
                    item.carousel = body["carousel"]
                    item.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


def upload_file(path, key):
    config = CosConfig(Region=settings.COS_REGION, SecretId=settings.COS_SECRET_ID, SecretKey=settings.COS_SECRET_KEY)
    client = CosS3Client(config)
    response = client.upload_file(
        Bucket='***REMOVED***',
        LocalFilePath=path,
        Key=key
    )
    return "https://{0}.cos.{1}.myqcloud.com/{2}".format(settings.COS_BUCKET, settings.COS_REGION, key)


def delete_file(key):
    config = CosConfig(Region=settings.COS_REGION, SecretId=settings.COS_SECRET_ID, SecretKey=settings.COS_SECRET_KEY)
    client = CosS3Client(config)
    response = client.delete_object(Bucket=settings.COS_BUCKET, Key=key)


@csrf_exempt
def files(request):
    try:
        token = request.headers['token']
        user = token_check(token, '***REMOVED***')
        if user:
            if request.method == "POST":
                file = request.FILES.get("file")
                type, suffix = str(file.content_type).split('/')
                time = timezone.now().__format__("%Y_%m_%d")
                filename = time + '_' + random_str(15) + '.' + suffix
                type_folder = os.path.join(settings.MEDIA_ROOT, type)
                folder = os.path.join(type_folder, str(user.id))
                if not os.path.exists(type_folder):
                    os.mkdir(type_folder)
                    os.mkdir(folder)
                elif not os.path.exists(folder):
                    os.mkdir(folder)
                path = os.path.join(folder, filename)
                with open(path, 'wb') as f:
                    for i in file.chunks():
                        f.write(i)
                key = 'files/{}/{}/'.format(type, user.id) + timezone.now().__format__("%Y/%m/%d/") + \
                      filename.split('_')[-1]
                url = upload_file(path, key)
                return JsonResponse({"url": url}, status=200)
            elif request.method == 'DELETE':
                body = demjson.decode(request.body)
                try:
                    suffix = body['url'].split('/', 3)[-1]
                    type = suffix.split('/', 2)[0]
                    id = suffix.split('/', 2)[1]
                    if user.id == id or user.is_superuser():
                        filename = suffix.split('/', 2)[2]
                        filename = '_'.join(filename.split('/'))
                        path = os.path.join(settings.MEDIA_ROOT, type, id, filename)
                        if os.path.exists(path):
                            os.remove(path)
                            delete_file(suffix)
                            return JsonResponse({}, status=200)
                        else:
                            return JsonResponse({"msg": "文件不存在"}, status=500)
                    else:
                        return JsonResponse({}, status=401)
                except Exception as e:
                    return JsonResponse({},status=404)
        else:
            return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def openUrl(request, type, id, Y, M, D, X):
    try:
        filename = '{}_{}_{}_{}'.format(Y, M, D, X)
        path = os.path.join(settings.MEDIA_ROOT, type, id, filename)
        if os.path.exists(path):
            with open(path.encode('utf-8'), 'rb') as f:
                response = HttpResponse(f.read(), content_type="application/octet-stream")
                response['Content-Disposition'] = 'attachment; filename={}'.format(X)
                return response
        else:
            return JsonResponse({}, status=500)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


if Website.objects.count() == 0:
    Website.objects.create()
try:
    def random_word_of_the_day():
        all = Word.objects.all()
        item = Website.objects.get(id=1)
        item.word_of_the_day = random.choice(all).id
        item.save()
        print('update word of the day at 0:00')


    try:
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), 'default')
        register_job(scheduler, 'cron', id='random_word_of_the_day', hour=0) \
            (random_word_of_the_day)
        register_events(scheduler)
        scheduler.start()
    except Exception:
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), 'default')
        register_job(scheduler, 'cron', id='random_word_of_the_day', hour=0, replace_existing=True) \
            (random_word_of_the_day)
        register_events(scheduler)
        scheduler.start()
except Exception as e:
    print(str(e))
