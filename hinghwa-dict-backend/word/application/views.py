import demjson
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from article.models import Article
from website.views import (
    token_check,
    sendNotification,
)
from ..forms import ApplicationForm
from ..models import Word, Application
from word.application.dto.application_simple import application_simple
from word.application.dto.application_all import application_all


@csrf_exempt
def searchApplication(request):
    try:
        # WD0403 查看多个申请
        if request.method == "GET":
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY, -1)
            if user:
                applications = Application.objects.filter(verifier__isnull=True)
                result = []
                for application in applications:
                    result.append(application_simple(application))
                return JsonResponse({"applications": result}, status=200)
            else:
                return JsonResponse({}, status=401)
        # WD0401 申请更新
        elif request.method == "POST":
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY)
            if user:
                body = demjson.decode(request.body)
                if "word" in body["content"]:
                    body["content_word"] = body["content"]["word"]
                    body["content"].pop("word")
                body.update(body["content"])
                application_form = ApplicationForm(body)
                word = Word.objects.filter(id=body["word"])
                if word.exists() or ~body["word"]:
                    if application_form.is_valid() and isinstance(
                        body["mandarin"], list
                    ):
                        for id in body["related_articles"]:
                            Article.objects.get(id=id)
                        for id in body["related_words"]:
                            Word.objects.get(id=id)
                        application = application_form.save(commit=False)
                        application.contributor = user
                        if word.exists():
                            word = word[0]
                            application.word = word
                        application.save()
                        for id in body["related_articles"]:
                            article = Article.objects.get(id=id)
                            application.related_articles.add(article)
                        for id in body["related_words"]:
                            wordx = Word.objects.get(id=id)
                            application.related_words.add(wordx)
                        return JsonResponse({"id": application.id}, status=200)
                    else:
                        return JsonResponse({}, status=400)
                else:
                    return JsonResponse({}, status=404)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)

    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


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
