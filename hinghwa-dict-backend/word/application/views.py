import demjson3
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from article.models import Article
from utils.exception.types.bad_request import BadRequestException
from utils.exception.types.common import CommonException
from utils.exception.types.not_found import (
    ApplicationNotFoundException,
    ArticleNotFoundException,
    WordNotFoundException,
)
from utils.TypeCheking import islist
from utils.token import token_pass, token_user
from website.views import sendNotification
from ..forms import ApplicationForm
from ..models import Word, Application
from word.application.dto.application_simple import application_simple
from word.application.dto.application_all import application_all


class MultiApplication(View):
    def get(self, request) -> JsonResponse:
        """
        WD0403 查看多个申请
        """
        token_pass(request.headers, -1)  # 仅限管理员
        applications = Application.objects.filter(verifier__isnull=True)
        result = []
        for application in applications:
            result.append(application_simple(application))
        return JsonResponse({"applications": result}, status=200)

    def post(self, request) -> JsonResponse:
        """
        WD0401 申请更新
        """
        try:
            user = token_user(token_pass(request.headers, 0))  # user = 操作用户
            body = demjson3.decode(request.body)  # body = 申请内容

            # 检查申请修改的词语是否存在（为0表示新建词语）
            word = Word.objects.filter(id=body["word"])
            if not word.exists() and not body["word"] == 0:
                raise WordNotFoundException(body["word"])

            # 检查修改申请是否合法
            if "word" in body["content"]:
                body["content_word"] = body["content"]["word"]
                body["content"].pop("word")
            body.update(body["content"])
            application_form = ApplicationForm(body)
            if not (application_form.is_valid() and islist(body["mandarin"])):
                raise BadRequestException()
            for id in body["related_articles"]:
                try:
                    Article.objects.get(id=id)
                except Article.DoesNotExist:
                    raise ArticleNotFoundException(id)
            for id in body["related_words"]:
                try:
                    Word.objects.get(id=id)
                except Word.DoesNotExist:
                    raise WordNotFoundException(id)

            # 构建申请
            application = application_form.save(commit=False)
            application.contributor = user
            if word.exists():
                word = word[0]
                application.word = word
            application.save()
            for id in body["related_articles"]:
                application.related_articles.add(Article.objects.get(id=id))
            for id in body["related_words"]:
                application.related_words.add(Word.objects.get(id=id))
            application.save()

            return JsonResponse({"id": application.id}, status=200)
        except CommonException as e:
            raise e


def find_application(id) -> Application:
    """
    查找申请
    """
    application = Application.objects.filter(id=id)
    if not application.exists():
        raise ApplicationNotFoundException(id)
    return application[0]


class SingleApplication(View):
    def get(self, request, id) -> JsonResponse:
        """
        WD0402 查看单个申请
        """
        application = find_application(id)
        token_pass(request.headers, application.contributor.id)  # 仅限申请人
        return JsonResponse({"application": application_all(application)}, status=200)

    def put(self, request, id) -> JsonResponse:
        """
        WD0404 修改申请
        """
        user = token_user(
            token_pass(request.headers, -1)
        )  # user = 操作用户（仅限管理员）
        application = find_application(id)
        application.verifier = user
        feedback = None
        body = demjson3.decode(request.body)  # body = 申请内容
        if not "result" in body:
            raise BadRequestException("缺少result字段")

        if body["result"]:
            # 通过申请
            if application.word:
                # 修改词语
                word = application.word
                content = (
                    f"您对 词语(id={application.word.id}) 提出的修改建议申请(id={application.id}) 已通过"
                    f"，感谢您为社区所做的贡献！"
                )
                title = "【通知】词条修改申请审核结果"
            else:
                # 新建词语
                word = Word.objects.create(
                    contributor=application.contributor, visibility=True
                )
                application.word = word
                content = (
                    f"您的创建 申请(id={application.id}) 已通过，"
                    f"已创建 词条(id={word.id}) ，感谢您为社区所做的贡献！"
                )
                title = "【通知】词条创建申请审核结果"
            attributes = [
                "definition",
                "annotation",
                "standard_ipa",
                "standard_pinyin",
                "mandarin",
            ]
            for attribute in attributes:
                value = getattr(application, attribute)
                setattr(word, attribute, value)
            word.word = application.content_word
            word.related_articles.clear()
            for related_article in application.related_articles.all():
                word.related_articles.add(related_article)
            word.related_words.clear()
            for related_word in application.related_words.all():
                word.related_words.add(related_word)
            word.save()
            feedback = word.id
        else:
            # 拒绝申请
            title = "【通知】词条修改申请审核结果"
            if application.word:
                # 修改词语
                content = (
                    f"您对 词语(id={application.word.id}) 提出的修改建议 申请(id={application.id})"
                    f'未能通过审核，理由是:\n\t{body["reason"]}\n感谢您为社区所做的贡献！'
                )
                feedback = application.word.id
            else:
                # 新建词语
                content = (
                    f"您的词语创建 申请(id={application.id}) 未能通过审核，"
                    f'理由是:\n\t{body["reason"]}\n感谢您为社区所做的贡献！'
                )
        application.save()

        # 发送通知
        sendNotification(
            None,
            [application.contributor],
            content,
            target=application,
            title=title,
            action_object=application.word,
        )
        return JsonResponse({"word": feedback}, status=200)
