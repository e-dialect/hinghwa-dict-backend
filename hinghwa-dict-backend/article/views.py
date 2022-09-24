import demjson
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from website.views import (
    evaluate,
    token_check,
    simpleUserInfo,
    filterInOrder,
    sendNotification,
)
from .forms import ArticleForm, CommentForm
from .models import Article, Comment
from django.conf import settings
from .dto.article_all import article_all
from .dto.article_normal import article_normal
from .dto.comment_normal import comment_normal
from django.views import View
from utils.exception.types.bad_request import BadRequestException
from utils.exception.types.not_found import ArticleNotFoundException
from utils.TokenCheking import token_pass, token_user


class SearchArticle(View):
    # AT0201 搜索符合条件的文章并返回id TODO 正式版search
    def get(self, request) -> JsonResponse:
        articles = list(Article.objects.filter(visibility=True))
        if "search" in request.GET:
            result = []
            key = request.GET["search"]
            for article in articles:
                if article.id == 148:
                    t = 1
                score = evaluate(
                    [
                        (article.author.username, 2),
                        (article.author.user_info.nickname, 2),
                        (article.title, 10),
                        (article.description, 8),
                        (article.content, 5),
                    ],
                    key,
                )
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

    # AT0101 创建新的文章
    def post(self, request) -> JsonResponse:
        token = token_pass(request.headers)
        user = token_user(token)
        body = demjson.decode(request.body)
        article_form = ArticleForm(body)
        if not article_form.is_valid():
            raise BadRequestException()
        article = article_form.save(commit=False)
        article.update_time = timezone.now()
        article.author = user
        article.save()
        content = f"我创建了文章(id={article.id}),请及时去审核"
        sendNotification(article.author, None, content, title="【提醒】文章待审核")
        return JsonResponse({"id": article.id}, status=200)

    # AT0202 文章内容批量获取
    def put(self, request) -> JsonResponse:
        token = token_pass(request.headers)
        body = demjson.decode(request.body)
        result = Article.objects.filter(id__in=body["articles"])
        user = token_user(token)
        if not user:
            result = result.filter(visibility=True)
        if not user.is_superuser:
            result = result.filter(visibility=True) | (result & user.articles.all())
        result = filterInOrder(result, body["articles"])
        articles = []
        for article in result:
            articles.append(
                {
                    "article": article_normal(article),
                    "author": simpleUserInfo(article.author),
                }
            )
        return JsonResponse({"articles": articles}, status=200)


class ManageArticle(View):
    # AT0104 获取文章内容
    def get(self, request, id) -> JsonResponse:
        token = token_pass(request.headers)
        user = token_user(token)
        article = Article.objects.filter(id=id)
        if not article.exists():
            raise ArticleNotFoundException()
        article = article[0]
        if (
            not article.visibility
            and not user.is_superuser
            and not user == article.author
        ):
            raise ArticleNotFoundException()
        article.views += 1
        article.save()
        me = (
            {
                "liked": article.like_users.filter(id=user.id).exists(),
                "is_author": user == article.author,
            }
            if user
            else {"liked": False, "is_author": False}
        )
        article = article_all(article)
        return JsonResponse({"article": article, "me": me}, status=200)

    # AT0103 更新文章内容
    def put(self, request, id) -> JsonResponse:
        article = Article.objects.filter(id=id)
        if not article.exists():
            raise ArticleNotFoundException()
        article = article[0]
        token = token_pass(request.headers, article.author.id)
        body = demjson.decode(request.body)
        body = body["article"]
        article_form = ArticleForm(body)
        for key in body:
            if len(article_form[key].errors.data):
                return JsonResponse({}, status=400)
        for key in body:
            setattr(article, key, body[key])
        article.update_time = timezone.now()
        article.visibility = False
        article.save()
        content = f"我修改了文章(id={article.id}),请及时去审核"
        sendNotification(article.author, None, content, title="【提醒】文章待审核")
        return JsonResponse({}, status=200)

    # AT0102 删除文章
    def delete(self, request, id) -> JsonResponse:
        article = Article.objects.filter(id=id)
        if not article.exists():
            raise ArticleNotFoundException()
        article = article[0]
        token = token_pass(request.headers, article.author.id)
        article.delete()
        return JsonResponse({}, status=200)


class ManageVisibility(View):
    # AT0105 文章审核
    def put(self, request, id) -> JsonResponse:
        token = token_pass(request.headers, -1)
        article = Article.objects.filter(id=id)
        if not article.exists():
            raise ArticleNotFoundException()
        article = article[0]
        body = demjson.decode(request.body)
        article.visibility = body["result"]
        if article.visibility:
            content = f"恭喜您的文章(id ={id}) 已通过审核"
        else:
            msg = body["reason"]
            content = f"您的文章(id = {id}) 审核状态变为不可见，理由是:\n\t{msg}"
        sendNotification(
            None,
            [article.author],
            content=content,
            target=article,
            title="【通知】文章审核结果",
        )
        article.save()
        return JsonResponse({}, status=200)


class LikeArticle(View):
    # AT0301 给这篇文章点赞
    def post(self, request, id) -> JsonResponse:
        token = token_pass(request.headers)
        user = token_user(token)
        article = Article.objects.filter(id=id)
        if not article.exists() or not article[0].visibility:
            raise ArticleNotFoundException()
        article = article[0]
        article.like_users.add(user)
        return JsonResponse({}, status=200)

    # AT0302 取消给这篇文章点赞
    def delete(self, request, id) -> JsonResponse:
        article = Article.objects.filter(id=id)
        if not article.exists() or not article[0].visibility:
            raise ArticleNotFoundException()
        article = article[0]
        token = token_pass(request.headers)
        user = token_user(token)
        if not len(article.like_users.filter(id=user.id)):
            raise BadRequestException()
        article.like_users.remove(user)
        return JsonResponse({}, status=200)


class CommentArticle(View):
    # AT0404 获取文章评论
    def get(self, request, id) -> JsonResponse:
        token = token_pass(request.headers)
        user = token_user(token)
        article = Article.objects.filter(id=id)
        if not article.exists() or not (
            article[0].visibility or user.is_superuser or user == article[0].author
        ):
            raise ArticleNotFoundException()
        article = article[0]
        comments = [comment_normal(comment) for comment in article.comments.all()]
        return JsonResponse({"comments": comments}, status=200)

    # AT0401 发表文章评论
    def post(self, request, id) -> JsonResponse:
        token = token_pass(request.headers)
        user = token_user(token)
        article = Article.objects.filter(id=id)
        if not article.exists() or not (
            article[0].visibility or user.is_superuser or user == article[0].author
        ):
            raise ArticleNotFoundException()
        article = article[0]
        body = demjson.decode(request.body)
        comment_form = CommentForm(body)
        if not comment_form.is_valid():
            raise BadRequestException()
        comment = comment_form.save(commit=False)
        comment.user = user
        comment.article = article
        if body["parent"] != 0:
            comment.parent = Comment.objects.get(id=body["parent"])
        comment.save()
        return JsonResponse({"id": comment.id}, status=200)

    # AT0402 删除文章评论（和子孙评论）
    def delete(self, request, id) -> JsonResponse:
        token = token_pass(request.headers)
        user = token_user(token)
        article = Article.objects.filter(id=id)
        if not article.exists() or not (
            article[0].visibility or user.is_superuser or user == article[0].author
        ):
            raise ArticleNotFoundException()
        body = demjson.decode(request.body)
        comment = Comment.objects.get(id=body["id"])
        if token_pass(request.headers, comment.user.id) or token_pass(
            request.headers, -1
        ):
            # 应原注释要求，超级管理员也能删
            comment.delete()
            return JsonResponse({}, status=200)


class SearchComment(View):
    # AT0403 评论内容批量获取
    def put(self, request) -> JsonResponse:
        body = demjson.decode(request.body)
        result = Comment.objects.filter(id__in=body["comments"])
        result = filterInOrder(result, body["comments"])
        comments = []
        for comment in result:
            comments.append(comment_normal(comment))
        return JsonResponse({"comments": comments}, status=200)


@csrf_exempt
def searchArticle(request):
    try:
        if request.method == "GET":
            # AT0201 搜索符合条件的文章并返回id TODO 正式版search
            articles = list(Article.objects.filter(visibility=True))
            if "search" in request.GET:
                result = []
                key = request.GET["search"]
                for article in articles:
                    if article.id == 148:
                        t = 1
                    score = evaluate(
                        [
                            (article.author.username, 2),
                            (article.author.user_info.nickname, 2),
                            (article.title, 10),
                            (article.description, 8),
                            (article.content, 5),
                        ],
                        key,
                    )
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
        elif request.method == "POST":
            body = demjson.decode(request.body)
            # AT0101 创建新的文章
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY)
            if user:
                article_form = ArticleForm(body)
                if article_form.is_valid():
                    article = article_form.save(commit=False)
                    article.update_time = timezone.now()
                    article.author = user
                    article.save()
                    content = f"我创建了文章(id={article.id}),请及时去审核"
                    sendNotification(article.author, None, content, title="【提醒】文章待审核")
                    return JsonResponse({"id": article.id}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        elif request.method == "PUT":
            # AT0202 文章内容批量获取
            body = demjson.decode(request.body)
            result = Article.objects.filter(id__in=body["articles"])
            user = 0
            if "token" in request.headers:
                token = request.headers["token"]
                user = token_check(token, settings.JWT_KEY)
                if user:
                    if not user.is_superuser:
                        result = result.filter(visibility=True) | (
                            result & user.articles.all()
                        )
            if not user:
                result = result.filter(visibility=True)
            result = filterInOrder(result, body["articles"])
            articles = []
            for article in result:
                articles.append(
                    {
                        "article": article_normal(article),
                        "author": simpleUserInfo(article.author),
                    }
                )
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
            token = request.headers["token"]
            # AT0104 获取文章内容
            if request.method == "GET":
                user = token_check(token, settings.JWT_KEY)
                if article.visibility or user.is_superuser or user == article.author:
                    article.views += 1
                    article.save()
                    me = (
                        {
                            "liked": article.like_users.filter(id=user.id).exists(),
                            "is_author": user == article.author,
                        }
                        if user
                        else {"liked": False, "is_author": False}
                    )
                    article = article_all(article)
                    return JsonResponse({"article": article, "me": me}, status=200)
                else:
                    return JsonResponse({}, status=404)
            # AT0103 更新文章内容
            elif request.method == "PUT":
                if token_check(token, settings.JWT_KEY, article.author.id):
                    body = demjson.decode(request.body)
                    body = body["article"]
                    article_form = ArticleForm(body)
                    for key in body:
                        if len(article_form[key].errors.data):
                            return JsonResponse({}, status=400)
                    for key in body:
                        setattr(article, key, body[key])
                    article.update_time = timezone.now()
                    article.visibility = False
                    article.save()
                    content = f"我修改了文章(id={article.id}),请及时去审核"
                    sendNotification(article.author, None, content, title="【提醒】文章待审核")
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
            # AT0102 删除文章
            elif request.method == "DELETE":
                if token_check(token, settings.JWT_KEY, article.author.id):
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
def manageArticleVisibility(request, id):
    try:
        # WD0404 文章审核
        if request.method == "PUT":
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY, -1)
            if user:
                article = Article.objects.filter(id=id)
                if article.exists():
                    article = article[0]
                    body = demjson.decode(request.body)
                    article.visibility = body["result"]
                    if article.visibility:
                        content = f"恭喜您的文章(id ={id}) 已通过审核"
                    else:
                        msg = body["reason"]
                        content = f"您的文章(id = {id}) 审核状态变为不可见，理由是:\n\t{msg}"
                    sendNotification(
                        None,
                        [article.author],
                        content=content,
                        target=article,
                        title="【通知】文章审核结果",
                    )
                    article.save()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=404)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def like(request, id):
    try:
        article = Article.objects.filter(id=id)
        if article.exists() and article[0].visibility:
            article = article[0]
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY)
            if user:
                # AT0301 给这篇文章点赞
                if request.method == "POST":
                    article.like_users.add(user)
                    return JsonResponse({}, status=200)
                # AT0302 取消给这篇文章点赞
                elif request.method == "DELETE":
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
        token = request.headers["token"]
        user = token_check(token, settings.JWT_KEY)
        if article.exists() and (
            article[0].visibility or user.is_superuser or user == article[0].author
        ):
            article = article[0]
            # AT0404 获取文章评论
            if request.method == "GET":
                comments = [
                    comment_normal(comment) for comment in article.comments.all()
                ]
                return JsonResponse({"comments": comments}, status=200)
            # AT0401 发表文章评论
            elif request.method == "POST":
                token = request.headers["token"]
                user = token_check(token, settings.JWT_KEY)
                if user:
                    body = demjson.decode(request.body)
                    comment_form = CommentForm(body)
                    if comment_form.is_valid():
                        comment = comment_form.save(commit=False)
                        comment.user = user
                        comment.article = article
                        if body["parent"] != 0:
                            comment.parent = Comment.objects.get(id=body["parent"])
                        comment.save()
                        return JsonResponse({"id": comment.id}, status=200)
                    else:
                        return JsonResponse({}, status=400)
                else:
                    return JsonResponse({}, status=401)
            # AT0402 删除文章评论（和子孙评论）
            elif request.method == "DELETE":
                body = demjson.decode(request.body)
                token = request.headers["token"]
                comment = Comment.objects.get(id=body["id"])
                if token_check(token, settings.JWT_KEY, comment.user.id):
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
        # AT0403 评论内容批量获取
        if request.method == "PUT":
            body = demjson.decode(request.body)
            result = Comment.objects.filter(id__in=body["comments"])
            result = filterInOrder(result, body["comments"])
            comments = []
            for comment in result:
                comments.append(comment_normal(comment))
            return JsonResponse({"comments": comments}, status=200)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)
