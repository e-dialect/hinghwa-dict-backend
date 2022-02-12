import math
import os
import random
import urllib.request

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
# from pydub import AudioSegment as audio
from notifications.signals import notify
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

from article.models import Article
from word.models import Word
from .forms import DailyExpressionForm
from .models import Website, DailyExpression


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


token_dict = {}


def token_register(token):
    token_dict[token] = timezone.now()
    if len(token_dict) > 1e4:
        now = timezone.now()
        ls = token_dict.items()
        for key, value in ls:
            if (now - value).seconds > 6000:
                token_dict.pop(key)


def token_check(token, key, id=0):
    '''
    id=-1表示要求管理员权限
    id=x表示用户id需要为x
    id=0表示任意用户都允许通过，
    成功满足要求的验证则自动刷新时长，100分钟未操作则自动超时
    :param token:
    :param key:
    :param id:
    :return:
    '''
    try:
        info = jwt.decode(token, key, algorithms=['HS256'])
        if (token in token_dict) and (timezone.now() - token_dict[token]).seconds > 6000:
            token_dict.pop(token)
            return 0
        user = User.objects.get(id=info['id'])
        if user.username == info['username'] and (id == 0 or id == info['id'] or user.is_superuser):
            token_dict[token] = timezone.now()
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


def ReLu(x: float):
    return x if x < 50 else (x - 50) * 0.01 + 50


def evaluate(standard, key):
    total = 0
    key = str(key).lower()
    for item, score in standard:
        item = str(item).lower()
        if len(item) > 0:
            total += (compare(item, key) + compare(item[::-1], key[::-1])) * score / math.log(1 + ReLu(len(item)))
    return total


def random_str(n=6, digit_only=False):
    if not digit_only:
        _str = '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    else:
        _str = '1234567890'
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
            code = random_str(digit_only=True)
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
            announcements = [0] * len(articles)
            a = {}
            num = 0
            for i in articles:
                a[i.id] = num
                num += 1
            for article in articles:
                announcements[a[article.id]] = {
                    'article': {"id": article.id, "likes": article.like_users.count(), 'author': article.author.id,
                                "views": article.views,
                                "publish_time": article.publish_time.__format__('%Y-%m-%d %H:%M:%S'),
                                "update_time": article.update_time.__format__('%Y-%m-%d %H:%M:%S'),
                                "title": article.title, "description": article.description, "content": article.content,
                                "cover": article.cover},
                    'author': {'id': article.author.id, 'nickname': article.author.user_info.nickname,
                               'avatar': article.author.user_info.avatar}}
            result = []
            for item in announcements:
                if item:
                    result.append(item)
            return JsonResponse({"announcements": result}, status=200)
        elif request.method == "PUT":
            body = demjson.decode(request.body)
            token = request.headers['token']
            if token_check(token, settings.JWT_KEY, -1):
                if isinstance(body['announcements'], list):
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
            hot_articles = [0] * len(articles)
            a = {}
            num = 0
            for i in articles:
                a[i.id] = num
                num += 1
            for article in articles:
                hot_articles[a[article.id]] = {
                    'article': {"id": article.id, "likes": article.like_users.count(), 'author': article.author.id,
                                "views": article.views,
                                "publish_time": article.publish_time.__format__('%Y-%m-%d %H:%M:%S'),
                                "update_time": article.update_time.__format__('%Y-%m-%d %H:%M:%S'),
                                "title": article.title, "description": article.description, "content": article.content,
                                "cover": article.cover},
                    'author': {'id': article.author.id, 'nickname': article.author.user_info.nickname,
                               'avatar': article.author.user_info.avatar}}
            result = []
            for item in hot_articles:
                if item:
                    result.append(item)
            return JsonResponse({"hot_articles": result}, status=200)
        elif request.method == "PUT":
            body = demjson.decode(request.body)
            token = request.headers['token']
            if token_check(token, settings.JWT_KEY, -1):
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
            if token_check(token, settings.JWT_KEY, -1):
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
            if token_check(token, settings.JWT_KEY, -1):
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


def download_file(url, local_path, filename):
    try:
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        path = os.path.join(local_path, filename)
        fd = open(path, 'w')
        fd.close()
        urllib.request.urlretrieve(url, filename=path)
        key = 'files/download/' + timezone.now().__format__("%Y/%m/%d/") + \
              filename.split('_')[-1]
        url = upload_file(path, key)
        return url
    except Exception as e:
        print("Error occurred when downloading file, error message:")
        print(e)
        return None


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
        user = token_check(token, settings.JWT_KEY)
        if user:
            if request.method == "POST":
                file = request.FILES.get("file")
                type = str(file.content_type).split('/')[0]
                suffix = file._name.rsplit('.')[-1]
                time = timezone.now().__format__("%Y_%m_%d")
                filename = time + '_' + random_str(15) + '.' + suffix
                type_folder = os.path.join(settings.MEDIA_ROOT, type)
                folder = os.path.join(type_folder, str(user.id))
                if not os.path.exists(type_folder):
                    os.mkdir(type_folder)
                    os.mkdir(folder)
                elif not os.path.exists(folder):
                    os.mkdir(folder)
                # if type != 'audio':
                path = os.path.join(folder, filename)
                with open(path, 'wb') as f:
                    for i in file.chunks():
                        f.write(i)
                # else:
                #     music = audio.from_file(file)
                #     path = os.path.join(folder, filename)
                #     music.set_frame_rate(44100)
                #     music.export(path, format='mp3')
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


    def register(fun, id, replace_existing):
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), 'default')
        register_job(scheduler, 'cron', id=id, hour=0, replace_existing=replace_existing) \
            (fun)
        register_events(scheduler)
        scheduler.start()


    try:
        register(random_word_of_the_day, 'random_word_of_the_day', False)
    except Exception:
        register(random_word_of_the_day, 'random_word_of_the_day', True)
except Exception as e:
    print(str(e))
from django.db.models import Q


@csrf_exempt
def searchDailyExpression(request):
    try:
        if request.method == 'GET':
            if 'keyword' in request.GET:
                key = request.GET['keyword']
                words = DailyExpression.objects.filter(
                    Q(english__icontains=key) |
                    Q(character__icontains=key) |
                    Q(pinyin__icontains=key) |
                    Q(mandarin__icontains=key))
            else:
                words = DailyExpression.objects.all()
            pageSize = int(request.GET['pageSize'])
            page = int(request.GET['page'])
            r = min(len(words), page * pageSize)
            l = min(len(words) + 1, (page - 1) * pageSize)
            results = []
            for word in words[l:r]:
                results.append({
                    'key': word.id, 'english': word.english,
                    'mandarin': word.mandarin, 'character': word.character,
                    'pinyin': word.pinyin
                })
            return JsonResponse({
                "results": results,
                "total": {
                    "page": (len(words) - 1) // pageSize + 1,
                    "item": len(words)
                }
            }, status=200)
        elif request.method == 'POST':
            token = request.headers['token']
            user = token_check(token, settings.JWT_KEY, -1)
            if user:
                body = demjson.decode(request.body)
                word_form = DailyExpressionForm(body)
                if word_form.is_valid():
                    word = word_form.save(commit=False)
                    word.save()
                    return JsonResponse({
                        'result': {
                            'key': word.id, 'english': word.english,
                            'mandarin': word.mandarin, 'character': word.character,
                            'pinyin': word.pinyin
                        }
                    }, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as msg:
        return JsonResponse({'msg': str(msg)}, status=500)


@csrf_exempt
def manageDailyExpression(request, id):
    try:
        token = request.headers['token']
        user = token_check(token, settings.JWT_KEY, -1)
        if user:
            word = DailyExpression.objects.filter(id=id)
            if word.exists():
                word = word[0]
                if request.method == 'PUT':
                    body = demjson.decode(request.body)
                    for property in body['daily_expression']:
                        setattr(word, property, body['daily_expression'][property])
                    word.save()
                    return JsonResponse({
                        'daily_expression': {
                            'key': word.id, 'english': word.english,
                            'mandarin': word.mandarin, 'character': word.character,
                            'pinyin': word.pinyin
                        }
                    }, status=200)
                elif request.method == 'DELETE':
                    word.delete()
                    return JsonResponse({}, status=204)
                else:
                    return JsonResponse({}, status=405)
            else:
                return JsonResponse({}, status=404)
        else:
            return JsonResponse({}, status=401)
    except Exception as msg:
        return JsonResponse({'msg': str(msg)}, status=500)


from notifications.models import Notification


def sendNotification(sender, recipients, content, target=None, action_object=None, title=None):
    if recipients is None:
        transfer = User.objects.get(id=2)
        result = sendNotification(sender, [transfer], content, target, action_object, title)
        recipients = User.objects.filter(is_superuser=True)
        target = Notification.objects.get(id=result[0])
        sendNotification(transfer, recipients, content, target, action_object, title)
        return result
    if title is None:
        title = f'【通知】{sender.username} 回复了你'
    try:
        len(recipients)
    except Exception as e:
        recipients = [recipients]
    result = notify.send(
        sender,
        recipient=recipients,
        verb=title,
        description=content,
        target=target,
        action_object=action_object,
    )
    return [note.id for note in result[0][1]]


def readNotification(notification):
    if isinstance(notification.target, Notification):
        notification.target.unread = False
        notification.target.save()
        Notification.objects.filter(
            Q(target_content_type=notification.target_content_type) &
            Q(target_object_id=notification.target_object_id)
        ).mark_all_as_read()
    else:
        notification.unread = False
        notification.save()


@csrf_exempt
def Notifications(request):
    try:
        token = request.headers['token']
        user = token_check(token, settings.JWT_KEY)
        if request.method == 'POST':
            body = demjson.decode(request.body)
            if user:
                if len(body['recipients']) == 1 and body['recipients'][0] == -1:
                    recipients = None
                else:
                    recipients = User.objects.filter(id__in=body['recipients'])
                title = body['title'] if 'title' in body else None
                notifications = sendNotification(user, recipients, body['content'], title=title)
                return JsonResponse({'notifications': notifications}, status=200)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as msg:
        return JsonResponse({'msg': str(msg)}, status=500)


@csrf_exempt
def manageNotification(request, id):
    try:
        notification = Notification.objects.filter(id=id)
        if notification.exists():
            notification = notification[0]
            if request.method == 'GET':
                token = request.headers['token']
                user1 = token_check(token, settings.JWT_KEY, notification.actor_object_id)
                user2 = token_check(token, settings.JWT_KEY, notification.recipient_id)
                if user1 or user2:
                    if user2 and user2.id == notification.recipient_id:
                        readNotification(notification)
                    return JsonResponse({
                        'from': notification.actor_object_id,
                        'to': notification.recipient_id,
                        'time': notification.timestamp.__format__('%Y-%m-%d %H:%M:%S'),
                        'title': notification.verb,
                        'content': notification.description,
                        'public': notification.public}, status=200)
                else:
                    return JsonResponse({}, status=401)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=404)
    except Exception as msg:
        return JsonResponse({'msg': str(msg)}, status=500)


@csrf_exempt
def manageNotificationUnread(request):
    try:
        token = request.headers['token']
        user = token_check(token, settings.JWT_KEY)
        if user:
            if request.method == 'PUT':
                body = demjson.decode(request.body) if len(request.body) else {}
                notifications = Notification.objects.filter(recipient_id=user.id)
                if 'notifications' in body:
                    notifications = notifications.filter(id__in=body['notifications'])
                for notification in notifications:
                    readNotification(notification)
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=401)
    except Exception as msg:
        return JsonResponse({'msg': str(msg)}, status=500)


@csrf_exempt
def test(request):
    body = demjson.decode(request.body)
    # notify.send(
    #     User.objects.get(id=body['actor']),
    #     recipient=User.objects.filter(is_superuser=True),
    #     verb='one more try',
    #     description='为啥有这个字段',
    #     target=Article.objects.get(id=2),
    #     action_object=Comment.objects.get(id=8),
    # )
    user = User.objects.get(id=1)
    a = Notification.objects.filter(actor_object_id=1)
    return JsonResponse({}, status=200)
