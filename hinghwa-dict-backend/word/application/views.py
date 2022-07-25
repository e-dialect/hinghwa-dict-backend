import demjson
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from article.models import Article
from utils.exception.types.bad_request import BadRequestExcption
from utils.exception.types.common import CommonException
from utils.exception.types.not_found import WordNotFoundExcption
from utils.TypeCheking import islist
from utils.TokenCheking import token_pass, token_user
from website.views import (
    token_check,
    sendNotification,
)
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
        print("okk")
        applications = Application.objects.filter(verifier__isnull=True)
        result = []
        print("okk")
        for application in applications:
            result.append(application_simple(application))
        return JsonResponse({"applications": result}, status=200)

    def post(self, request) -> JsonResponse:
        """
        WD0401 申请更新
        """
        try:
            token = token_pass(request.headers, 0)
            user = token_user(token)  # user = 操作用户
            body = demjson.decode(request.body)  # body = 申请内容

            # 检查申请修改的词语是否存在（为0表示新建词语）
            word = Word.objects.filter(id=body["word"])
            if not word.exists() and not body["word"] == 0:
                raise WordNotFoundExcption(body["word"])

            # 检查修改申请是否合法
            if "word" in body["content"]:
                body["content_word"] = body["content"]["word"]
                body["content"].pop("word")
            body.update(body["content"])
            application_form = ApplicationForm(body)
            if not (application_form.is_valid() and islist(body["mandarin"])):
                raise BadRequestExcption()

            # 构建申请
            application = application_form.save(commit=False)
            application.contributor = user
            if word.exists():
                word = word[0]
                application.word = word
            for id in body["related_articles"]:
                application.related_articles.add(Article.objects.get(id=id))
            for id in body["related_words"]:
                application.related_words.add(Word.objects.get(id=id))
            application.save()

            return JsonResponse({"id": application.id}, status=200)
        except CommonException as e:
            raise e
        except Exception as e:
            raise BadRequestExcption(repr(e))


@csrf_exempt
def manageApplication(request, id):
    try:
        application = Application.objects.filter(id=id)
        if application.exists():
            application = application[0]
            # WD0402 查看单个申请内容
            if request.method == "GET":
                token = request.headers["token"]
                user = token_check(token, settings.JWT_KEY, application.contributor.id)
                if user:
                    return JsonResponse(
                        {"application": application_all(application)}, status=200
                    )
                else:
                    return JsonResponse({}, status=401)
            # WD0404 审核申请
            elif request.method == "PUT":
                token = request.headers["token"]
                user = token_check(token, settings.JWT_KEY, -1)
                if user:
                    body = demjson.decode(request.body)
                    application.verifier = user
                    feedback = None
                    if body["result"]:
                        if application.word:
                            word = application.word
                            content = (
                                f"您对(id = {application.word.id}) 词语提出的修改建议(id = {application.id})已通过"
                                f"，感谢您为社区所做的贡献！"
                            )
                            title = "【通知】词条修改申请审核结果"
                        else:
                            word = Word.objects.create(
                                contributor=application.contributor, visibility=True
                            )
                            application.word = word
                            content = (
                                f"您的创建申请 (id = {application.id})已通过，"
                                f"已创建词条(id = {word.id})，感谢您为社区所做的贡献！"
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
                        if application.word:
                            content = (
                                f"您对(id = {application.word.id}) 词语提出的修改建议(id = {application.id})"
                                f'未能通过审核，理由是:\n\t{body["reason"]}\n感谢您为社区所做的贡献！'
                            )
                            feedback = application.word.id
                        else:
                            content = (
                                f"您的创建申请 (id = {application.id})未能通过审核，"
                                f'理由是:\n\t{body["reason"]}\n感谢您为社区所做的贡献！'
                            )
                        title = "【通知】词条修改申请审核结果"
                    sendNotification(
                        None,
                        [application.contributor],
                        content,
                        target=application,
                        title=title,
                    )
                    application.save()
                    return JsonResponse({"word": feedback}, status=200)
                else:
                    return JsonResponse({}, status=401)
            else:
                return JsonResponse({}, status=405)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)
