import demjson
from django.http import JsonResponse
from django.shortcuts import render
from website.views import token_check, filterInOrder
from django.conf import settings

# Create your views here.


from django.views.decorators.csrf import csrf_exempt
from .models import Quiz
from .forms import QuizForm
from .dto.quiz_all import quiz_all


@csrf_exempt
def manageQuiz(request):
    try:
        # QZ0102 增加单个测试
        if request.method == "POST":
            body = demjson.decode(request.body)
            token = request.headers["token"]
            # 暂时设置为需要管理员权限
            user = token_check(token, settings.JWT_KEY, -1)
            if user:
                quiz_form = QuizForm(body)
                if quiz_form.is_valid():
                    quiz = quiz_form.save(commit=False)
                    quiz.save()
                    return JsonResponse({"id": quiz.id}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        # QZ0201 搜索测试题
        # 注：默认搜索范围是所有测试题
        elif request.method == "GET":
            quizzes = Quiz.objects.all()
            # keywords此处默认对question进行模糊搜索
            if "keywords" in request.GET:
                quizzes = quizzes.filter(question__contains=request.GET["keywords"])
            quizzes = list(quizzes)
            result = [quiz for quiz in quizzes]
            return JsonResponse({"result": result}, status=200)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def searchQuiz(request, id):
    try:
        quiz = Quiz.objects.filter(id=id)
        if quiz.exists():
            quiz = quiz[0]
            # QZ0101 获取单个测试
            if request.method == "GET":
                return JsonResponse({"quiz": quiz_all(quiz)}, status=200)
            # QZ0103 修改单个测试
            elif request.method == "PUT":
                body = demjson.decode(request.body)
                token = request.headers["token"]
                user = token_check(token, settings.JWT_KEY, -1)
                if user:
                    body = body["quiz"]
                    quiz_form = QuizForm(quiz)
                    for key in body:
                        if len(quiz_form[key].errors.data):
                            return JsonResponse({}, status=400)
                    for key in body:
                        setattr(quiz, key, body[key])
                    quiz.save()
                    return JsonResponse({"quiz": quiz_all(quiz)}, status=200)
                else:
                    return JsonResponse({}, status=403)
            # QZ0104 删除单个测试
            elif request.method == "DELETE":
                token = request.headers["token"]
                user = token_check(token, settings.JWT_KEY, -1)
                if user:
                    quiz.delete()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=403)
        return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def randomQuiz(request):
    try:
        # QZ0202 随机测试题
        if request.method == "GET":
            quiz = Quiz.objects.order_by("?")[:1]
            return JsonResponse({"quiz": quiz_all(quiz)}, status=200)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)
