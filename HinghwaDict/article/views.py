import demjson
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from website.views import token_check
from .forms import ArticleForm, CommentForm
from .models import Article, Comment


@csrf_exempt
def searchArticle(request):
    body = demjson.decode(request.body)
    try:
        if request.method == 'GET':
            # 搜索符合条件的文章并返回id TODO 正式版search
            articles = list(Article.objects.all())
            articles.sort(key=lambda article: article.publish_time, reverse=True)
            articles = [article.id for article in articles]
            return JsonResponse({"articles": articles})
        elif request.method == 'POST':
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
            articles = []
            for id in body['articles']:
                article = Article.objects.get(id=id)
                articles.append({"id": article.id, "author": article.author.username,
                                 "likes": article.like_users.count(), "views": article.views,
                                 "publish_time": article.publish_time.__format__('%Y-%m-%d %H:%M:%S'),
                                 "update_time": article.update_time.__format__('%Y-%m-%d %H:%M:%S'),
                                 "title": article.title, "description": article.description, "content": article.content,
                                 "cover": article.cover})
            return JsonResponse({"articles": articles}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def manageArticle(request, id):
    try:
        body = demjson.decode(request.body)
        article = Article.objects.get(id=id)
        token = request.headers['token']
        if request.method == 'GET':
            article.views += 1
            user = token_check(token, 'dxw')
            me = {'liked': article.like_users.filter(id=user.id).exists(),
                  'is_author': user == article.author} if user else {'liked': False, 'is_author': False}
            user = article.author
            article = {"id": article.id, "author": {"id": user.id, 'username': user.username, 'nickname': info.nickname,
                                                    'email': user.email, 'telephone': user.user_info.telephone,
                                                    'registration_time': user.date_joined,
                                                    'login_time': user.last_login,
                                                    'birthday': user.user_info.birthday,
                                                    'avatar': user.user_info.avatar,
                                                    'county': user.user_info.county, 'town': user.user_info.town,
                                                    'is_admin': user.is_superuser},
                       "likes": article.like_users.count(), "views": article.views,
                       "publish_time": article.publish_time.__format__('%Y-%m-%d %H:%M:%S'),
                       "update_time": article.update_time.__format__('%Y-%m-%d %H:%M:%S'),
                       "title": article.title, "description": article.description, "content": article.content,
                       "cover": article.cover, "like_users": [x.id for x in article.like_users.all()]}
            return JsonResponse({"article": article, 'me': me}, status=200)
        elif request.method == 'PUT':
            if token_check(token, 'dxw', article.author.id):
                body = body['article']
                article_form = ArticleForm(body)
                for key in body:
                    if len(article_form[key].errors.data):
                        return JsonResponse({}, status=400)
                for key in body:
                    setattr(article, key, body[key])
                article.update_time = timezone.now()
                article.save()
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
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def like(request, id):
    try:
        body = demjson.decode(request.body)
        article = Article.objects.get(id=id)
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
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def comment(request, id):
    try:
        body = demjson.decode(request.body)
        article = Article.objects.get(id=id)
        if request.method == 'GET':
            comments = [{"id": comment.id,
                         "user": {"id": comment.user.id, "avatar": comment.user.user_info.avatar},
                         "content": comment.content,
                         "time": comment.time.__format__('%Y-%m-%d %H:%M:%S'),
                         "parent": comment.parent_id if comment.parent else 0} for comment in article.comments.all()]
            return JsonResponse({"comments": comments}, status=200)
        elif request.method == 'POST':
            token = request.headers['token']
            user = token_check(token, 'dxw')
            if user:
                comment_form = CommentForm(body)
                if comment_form.is_valid():
                    comment = comment_form.save(commit=False)
                    comment.user = user
                    comment.article = article
                    if 'parent' in body:
                        comment.parent = Comment.objects.get(id=body['parent'])
                    else:
                        comment.parent_id = 0
                    comment.save()
                    return JsonResponse({'id': comment.id}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        elif request.method == 'DELETE':
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
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)
