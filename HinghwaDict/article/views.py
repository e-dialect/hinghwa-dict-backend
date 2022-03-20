import demjson
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from website.views import evaluate, token_check, simpleUserInfo, filterInOrder, sendNotification
from .forms import ArticleForm, CommentForm
from .models import Article, Comment


@csrf_exempt
def searchArticle(request):
    try:
        if request.method == 'GET':
            # 搜索符合条件的文章并返回id TODO 正式版search
            articles = list(Article.objects.filter(visibility=True))
            if 'search' in request.GET:
                result = []
                key = request.GET['search']
                for article in articles:
                    if article.id == 148:
                        t = 1
                    score = evaluate([(article.author.username, 2), (article.author.user_info.nickname, 2),
                                      (article.title, 10), (article.description, 8), (article.content, 5)], key)
                    result.append((article.id, score))
                result.sort(key=lambda a: a[1], reverse=True)
                articles = []
                for id, score in result:
                    if score > 0:
                        articles.append(Article.objects.get(id=id))
                    else:
                        break
            else:
                articles.sort(key=lambda a: a.update_time, reverse=True)
            articles = [article.id for article in articles]
            return JsonResponse({"articles": articles})
        elif request.method == 'POST':
            body = demjson.decode(request.body)
            # 创建新的文章
            token = request.headers['token']
            user = token_check(token, 'dxw')
            if user:
                article_form = ArticleForm(body)
                if article_form.is_valid():
                    article = article_form.save(commit=False)
                    article.update_time = timezone.now()
                    article.author = user
                    article.save()
                    return JsonResponse({'id': article.id}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        elif request.method == 'PUT':
            # 批量返回文章内容
            body = demjson.decode(request.body)
            result = Article.objects.filter(id__in=body['articles'])
            user = 0
            if 'token' in request.headers:
                token = request.headers['token']
                user = token_check(token, 'dxw')
                if user:
                    if not user.is_superuser:
                        result = result.filter(visibility=True) | (result & user.articles.all())
            if not user:
                result = result.filter(visibility=True)
            result = filterInOrder(result, body['articles'])
            articles = []
            for article in result:
                articles.append({
                    'article': {"id": article.id, "likes": article.like(), 'author': article.author.id,
                                "views": article.views,
                                "publish_time": article.publish_time.__format__('%Y-%m-%d %H:%M:%S'),
                                "update_time": article.update_time.__format__('%Y-%m-%d %H:%M:%S'),
                                "title": article.title, "description": article.description, "content": article.content,
                                "cover": article.cover, 'visibility': article.visibility},
                    'author': simpleUserInfo(article.author)})
            return JsonResponse({"articles": articles}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def manageArticle(request, id):
    try:
        article = Article.objects.filter(id=id)
        if article.exists():
            article = article[0]
            token = request.headers['token']
            if request.method == 'GET':
                user = token_check(token, 'dxw')
                if article.visibility or user.is_superuser or user == article.author:
                    article.views += 1
                    article.save()
                    me = {'liked': article.like_users.filter(id=user.id).exists(),
                          'is_author': user == article.author} if user else {'liked': False, 'is_author': False}
                    user = article.author
                    article = {"id": article.id,
                               "author": {"id": user.id, 'username': user.username, 'nickname': user.user_info.nickname,
                                          'email': user.email, 'telephone': user.user_info.telephone,
                                          'registration_time': user.date_joined.__format__('%Y-%m-%d %H:%M:%S'),
                                          'login_time': user.last_login.__format__('%Y-%m-%d %H:%M:%S')
                                          if user.last_login else '',
                                          'birthday': user.user_info.birthday,
                                          'avatar': user.user_info.avatar,
                                          'county': user.user_info.county, 'town': user.user_info.town,
                                          'is_admin': user.is_superuser},
                               "likes": article.like(), "views": article.views,
                               "publish_time": article.publish_time.__format__('%Y-%m-%d %H:%M:%S'),
                               "update_time": article.update_time.__format__('%Y-%m-%d %H:%M:%S'),
                               "title": article.title, "description": article.description, "content": article.content,
                               "cover": article.cover, 'visibility': article.visibility,
                               "like_users": [x.id for x in article.like_users.all()]}
                    return JsonResponse({"article": article, 'me': me}, status=200)
                else:
                    return JsonResponse({}, status=404)
            elif request.method == 'PUT':
                if token_check(token, 'dxw', article.author.id):
                    body = demjson.decode(request.body)
                    body = body['article']
                    article_form = ArticleForm(body)
                    for key in body:
                        if len(article_form[key].errors.data):
                            return JsonResponse({}, status=400)
                    for key in body:
                        setattr(article, key, body[key])
                    article.update_time = timezone.now()
                    article.visibility = False
                    article.save()
                    content = f'我修改了文章(id={article.id}),请及时去审核'
                    sendNotification(article.author, None, content,title='【提醒】文章待审核')
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
            elif request.method == 'DELETE':
                if token_check(token, 'dxw', article.author.id):
                    article.delete()
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
def like(request, id):
    try:
        article = Article.objects.filter(id=id)
        if article.exists() and article[0].visibility:
            article = article[0]
            token = request.headers['token']
            user = token_check(token, 'dxw')
            if user:
                if request.method == 'POST':
                    article.like_users.add(user)
                    return JsonResponse({}, status=200)
                elif request.method == 'DELETE':
                    if len(article.like_users.filter(id=user.id)):
                        article.like_users.remove(user)
                    else:
                        return JsonResponse({}, status=400)
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=405)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def comment(request, id):
    try:
        article = Article.objects.filter(id=id)
        token = request.headers['token']
        user = token_check(token, 'dxw')
        if article.exists() and (article[0].visibility or user.is_superuser or user == article[0].author):
            article = article[0]
            if request.method == 'GET':
                comments = [{"id": comment.id,
                             "user": simpleUserInfo(comment.user),
                             "content": comment.content,
                             "time": comment.time.__format__('%Y-%m-%d %H:%M:%S'),
                             "parent": comment.parent_id if comment.parent else 0} for comment in
                            article.comments.all()]
                return JsonResponse({"comments": comments}, status=200)
            elif request.method == 'POST':
                token = request.headers['token']
                user = token_check(token, 'dxw')
                if user:
                    body = demjson.decode(request.body)
                    comment_form = CommentForm(body)
                    if comment_form.is_valid():
                        comment = comment_form.save(commit=False)
                        comment.user = user
                        comment.article = article
                        if body['parent'] != 0:
                            comment.parent = Comment.objects.get(id=body['parent'])
                        comment.save()
                        return JsonResponse({'id': comment.id}, status=200)
                    else:
                        return JsonResponse({}, status=400)
                else:
                    return JsonResponse({}, status=401)
            elif request.method == 'DELETE':
                body = demjson.decode(request.body)
                token = request.headers['token']
                comment = Comment.objects.get(id=body['id'])
                if token_check(token, 'dxw', comment.user.id):
                    # 应该超级管理员也能删除吧
                    comment.delete()
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
def searchComment(request):
    try:
        if request.method == 'PUT':
            body = demjson.decode(request.body)
            result = Comment.objects.filter(id__in=body['comments'])
            result = filterInOrder(result, body['comments'])
            comments = []
            for comment in result:
                comments.append({'id': comment.id, 'user': comment.user.id, 'content': comment.content,
                                 'time': comment.time.__format__('%Y-%m-%d %H:%M:%S'),
                                 'parent': comment.parent_id if comment.parent else 0,
                                 'article': comment.article.id})
            return JsonResponse({'comments': comments}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=500)
