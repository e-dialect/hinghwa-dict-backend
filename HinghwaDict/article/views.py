import demjson
import jwt
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .forms import ArticleForm, CommentForm
from .models import Article, Comment, User

@csrf_exempt
def searchArticle(request):
    body = demjson.decode(request.body)
    try:
        if request.method == 'GET':
            pass  # 搜索符合条件的文章并返回id
        elif request.method == 'POST':
            # 创建新的文章
            token = request.headers['token']
            user_form = jwt.decode(token, '***REMOVED***', algorithms=['HS256'])
            user = User.objects.get(id=user_form['id'])
            if user.username == user_form['username']:
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
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=400)


@csrf_exempt
def manageArticle(request, id):
    try:
        body = demjson.decode(request.body)
        article = Article.objects.get(id=id)
        if request.method == 'GET':
            article.views += 1
            article = {"id": article.id, "author": article.author.username,
                       "likes": article.like_users.count(), "views": article.views,
                       "publish_time": article.publish_time.__format__('%Y-%m-%d %H:%M:%S'),
                       "update_time": article.update_time.__format__('%Y-%m-%d %H:%M:%S'),
                       "title": article.title, "description": article.description, "content": article.content,
                       "cover": article.cover, "like_users": [x.id for x in article.like_users.all()]}
            return JsonResponse({"article": article}, status=200)
        elif request.method == 'PUT':
            token = request.headers['token']
            user_form = jwt.decode(token, '***REMOVED***', algorithms=['HS256'])
            user = User.objects.get(id=user_form['id'])
            if user.username == user_form['username'] and user == article.author:
                article_form = ArticleForm(body)
                for key in body:
                    if len(article_form[key].errors.data):
                        return JsonResponse({}, status=400)
                if "title" in body:
                    article.title = body['title']
                if "content" in body:
                    article.content = body['content']
                if "description" in body:
                    article.description = body['description']
                if "cover" in body:
                    article.cover = body['cover']
                article.update_time = timezone.now()
                article.save()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
        elif request.method == 'DELETE':
            token = request.headers['token']
            user_form = jwt.decode(token, '***REMOVED***', algorithms=['HS256'])
            user = User.objects.get(id=user_form['id'])
            if user.username == user_form['username'] and (user == article.author or user.is_superuser):
                # 应该超级管理员也能删除吧
                article.delete()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=400)


@csrf_exempt
def like(request, id):
    try:
        body = demjson.decode(request.body)
        article = Article.objects.get(id=id)
        token = request.headers['token']
        user_form = jwt.decode(token, '***REMOVED***', algorithms=['HS256'])
        user = User.objects.get(id=user_form['id'])
        if user.username == user_form['username']:
            if request.method == 'POST':
                article.like_users.add(user)
            elif request.method == 'DELETE':
                if len(article.like_users.filter(id=user.id)):
                    article.like_users.remove(user)
                else:
                    return JsonResponse({}, status=400)
            return JsonResponse({}, status=200)

        else:
            return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=400)


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
            user_form = jwt.decode(token, '***REMOVED***', algorithms=['HS256'])
            user = User.objects.get(id=user_form['id'])
            if user.username == user_form['username']:
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
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        elif request.method == 'DELETE':
            token = request.headers['token']
            user_form = jwt.decode(token, '***REMOVED***', algorithms=['HS256'])
            user = User.objects.get(id=user_form['id'])
            comment = Comment.objects.get(id=body['id'])
            if user.username == user_form['username'] and (user == comment.user or user.is_superuser):
                # 应该超级管理员也能删除吧
                comment.delete()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=400)
