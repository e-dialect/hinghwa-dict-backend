import demjson3
import datetime
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from website.views import (
    evaluate,
    token_check,
    simpleUserInfo,
    filterInOrder,
    sendNotification,
)
from .forms import ArticleForm, CommentForm
from django.db.models import Q, Count, Max
from user.dto.user_simple import user_simple
from .models import Article, Comment
from django.conf import settings
from .dto.article_all import article_all
from django.core.cache import caches
from .dto.article_normal import article_normal
from .dto.comment_normal import comment_normal
from .dto.comment_likes import comment_likes
from .dto.comment_all import comment_all
from django.views import View
from utils.exception.types.bad_request import (
    BadRequestException,
    ReturnUsersNumException,
    RankWithoutDays,
)
from django.core.paginator import Paginator
from utils.exception.types.not_found import (
    ArticleNotFoundException,
    CommentNotFoundException,
    NotFoundException,
)
from utils.exception.types.unauthorized import UnauthorizedException
from utils.token import token_pass, token_user
from utils.Rewards_action import manage_points_in_article


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
        body = demjson3.decode(request.body)
        article_form = ArticleForm(body)
        if not article_form.is_valid():
            raise BadRequestException()
        article = article_form.save(commit=False)
        article.update_time = timezone.now()
        article.author = user
        article.save()
        content = f"我创建了文章(id={article.id}),请及时审核"
        sendNotification(
            article.author,
            None,
            content,
            title="【提醒】文章待审核",
            action_object=article,
        )
        return JsonResponse({"id": article.id}, status=200)

    # AT0202 文章内容批量获取
    def put(self, request) -> JsonResponse:
        body = demjson3.decode(request.body)
        result = Article.objects.filter(id__in=body["articles"])
        try:
            token = token_pass(request.headers)
            user = token_user(token)
            if not user.is_superuser:
                result = result.filter(visibility=True)
        except UnauthorizedException:
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


class ManageArticle(View):
    # AT0104 获取文章内容
    def get(self, request, id) -> JsonResponse:
        article = Article.objects.filter(id=id)
        if not article.exists():
            raise ArticleNotFoundException()
        article = article[0]
        try:
            token = token_pass(request.headers)
            user = token_user(token)
        except UnauthorizedException:
            if not article.visibility:
                raise ArticleNotFoundException()
            else:
                article.views += 1
                article.save()
                article = article_all(article)
                me = {"liked": False, "is_author": False}
                return JsonResponse({"article": article, "me": me}, status=200)
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
        body = demjson3.decode(request.body)
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
        sendNotification(
            article.author,
            None,
            content,
            title="【提醒】文章待审核",
            action_object=article,
        )
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
        body = demjson3.decode(request.body)
        article.visibility = body["result"]
        if article.visibility:
            content = f"恭喜您的 文章(id={id}) 已通过审核"
            user_id = article.author.id
            transaction_info = manage_points_in_article(user_id)
        else:
            msg = body["reason"]
            content = f"您的 文章(id={id}) 审核状态变为不可见，理由是:\n\t{msg}"
        sendNotification(
            None,
            [article.author],
            content=content,
            action_object=article,
            title="【通知】文章审核结果",
        )
        article.save()
        return JsonResponse(transaction_info, status=200)


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
            raise NotFoundException("你还没有给文章点赞过，不能取消点赞")
        article.like_users.remove(user)
        return JsonResponse({"msg": "取消文章点赞成功"}, status=200)


class CommentArticle(View):
    # AT0404 获取文章评论
    def get(self, request, id) -> JsonResponse:
        user = User()
        try:
            token = token_pass(request.headers)
            user = token_user(token)
        except UnauthorizedException:
            pass

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
        body = demjson3.decode(request.body)
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
        body = demjson3.decode(request.body)
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
        body = demjson3.decode(request.body)
        result = Comment.objects.filter(id__in=body["comments"])
        result = filterInOrder(result, body["comments"])
        comments = []
        for comment in result:
            comments.append(comment_normal(comment))
        return JsonResponse({"comments": comments}, status=200)


class CommentDetail(View):
    # AT0405 获取评论详情
    def get(self, request, id) -> JsonResponse:
        try:
            comment = Comment.objects.get(id=id)
        except Comment.DoesNotExist:
            raise CommentNotFoundException(id)

        me = {"like": False}

        # token = token_pass(request.headers)
        user = request.user

        # 是否是评论的作者，未添加

        me["like"] = comment.like_users.filter(id=user.id).exists()

        return JsonResponse({"comment": comment_all(comment), "me": me}, status=200)


class LikeComment(View):
    # AT0406 给文章评论点赞
    def post(self, request, id) -> JsonResponse:
        token = token_pass(request.headers)
        user = token_user(token)
        comment = Comment.objects.filter(id=id)
        if not comment.exists():
            raise CommentNotFoundException(id)
        # 可能这边可以写一个已经点赞过来防范攻击？
        comment = comment[0]
        return_num = self.return_users_num_pass(request)  # 返回None或者整型数字
        comment.like_users.add(user)
        return JsonResponse(comment_likes(comment, return_num), status=200)

    # AT0407 取消文章评论点赞
    def delete(self, request, id) -> JsonResponse:
        token = token_pass(request.headers)
        user = token_user(token)
        comment = Comment.objects.filter(id=id)
        if not comment.exists():
            raise CommentNotFoundException(id)
        comment = comment[0]
        if not len(comment.like_users.filter(id=user.id)):
            raise NotFoundException("你还没有给评论点赞过，不能取消文章评论点赞")
        return_num = self.return_users_num_pass(request)  # 返回None或者整型数字
        comment.like_users.remove(user)
        return JsonResponse(comment_likes(comment, return_num), status=200)

    @classmethod
    def return_users_num_pass(self, request):
        if "return_users_num" in request.GET:
            if not request.GET["return_users_num"]:
                raise ReturnUsersNumException()
            request_num = int(request.GET["return_users_num"])
            if request_num < 0:
                raise ReturnUsersNumException()
            return int(request.GET["return_users_num"])
        return None


class ArticleRanking(View):
    # AT0203 文章上传榜单
    def get(self, request) -> JsonResponse:
        days = request.GET["days"]  # 要多少天的榜单
        page = request.GET.get("page", 1)  # 获取页面数，默认为第1页
        pagesize = request.GET.get("pageSize", 10)  # 获取每页显示数量，默认为10条
        if not days:
            raise RankWithoutDays()
        days = int(days)
        try:
            token = token_pass(request.headers)
            user: User = token_user(token)
            my_id = user.id
        except:
            my_id = 0
        my_amount = 0
        my_rank = 0
        rank_count = 0
        result_json_list = []
        paginator = Pages(self.get_rank_queries(days), pagesize)
        current_page = paginator.get_page(page)
        adjacent_pages = list(
            paginator.get_adjacent_pages(current_page, adjancent_pages=3)
        )

        for rank_q in self.get_rank_queries(days):
            con_id = rank_q["author_id"]
            amount = rank_q["article_count"]
            rank_count = rank_count + 1
            if con_id == my_id:
                my_amount = amount
                my_rank = rank_count
            result_json_list.append(
                {
                    "author": user_simple(User.objects.filter(id=con_id)[0]),
                    "amount": amount,
                }
            )
        # 发送给前端
        return JsonResponse(
            {
                "ranking": result_json_list,
                "me": {"amount": my_amount, "rank": my_rank},
                "pagination": {
                    "total_pages": paginator.num_pages,
                    "current_page": current_page.number,
                    "page_size": pagesize,
                    "previous_page": current_page.has_previous(),
                    "next_page": current_page.has_next(),
                    "adjacent_pages": adjacent_pages,
                },
            },
            status=200,
        )

    @classmethod
    def get_rank_queries(cls, days):
        rank_cache = caches["article_ranking"]
        rank_queries = rank_cache.get(str(days))
        if rank_queries is None:
            # 发现缓存中没有要查询的天数的榜单，更新榜单，并把更新的表格录入到数据库缓存中article_ranking表的对应位置
            rank_queries = cls.update_rank(days)
            rank_cache.set(str(days), rank_queries)
        return rank_queries

    @classmethod
    def update_rank(cls, search_days):  # 不包括存储在数据库中
        if search_days != 0:
            start_date = timezone.now() - datetime.timedelta(days=search_days)
            # 查询发布时间在规定开始时间之后的
            result = (
                Article.objects.filter(
                    Q(publish_time__gt=start_date) & Q(visibility=True)
                )
                .values("author_id")
                .annotate(
                    article_count=Count("author_id"),
                    last_date=Max("publish_time"),
                )
                .order_by("-article_count", "-last_date")
            )
        else:
            result = (
                Article.objects.filter(visibility=True)
                .values("author_id")
                .annotate(
                    article_count=Count("author_id"),
                    last_date=Max("publish_time"),
                )
                .order_by("-article_count", "-last_date")
            )
        return result  # 返回的是Queries


class Pages(Paginator):
    # 对原有的Paginator类进行扩展，获取当前页的相邻页面
    def get_adjacent_pages(self, current_page, adjancent_pages=3):
        current_page = current_page.number
        start_page = max(current_page - adjancent_pages, 1)  # 前面的页码数
        end_page = min(current_page + adjancent_pages, self.num_pages)  # 后面的页码数
        return range(start_page, end_page + 1)
