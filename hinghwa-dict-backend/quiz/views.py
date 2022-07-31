import demjson
from django.http import JsonResponse
from django.conf import settings
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from .models import Quiz
from .forms import QuizForm
from .dto.quiz_all import quiz_all
from utils.exception.types.bad_request import BadRequestException
from utils.exception.types.common import CommonException
from utils.exception.types.not_found import QuizNotFoundException
from utils.exception.types.forbidden import ForbiddenException
from utils.TokenCheking import token_pass, token_user


class SingleQuiz(View):
    # QZ0101 获取单个测试
    def get(self, request, id) -> JsonResponse:
        try:
            quiz = Quiz.objects.filter(id=id)
            if not quiz.exists():  # 404
                raise QuizNotFoundException()
            quiz = quiz[0]
            return JsonResponse({"quiz": quiz_all(quiz)}, status=200)
        except CommonException as e:  # 500
            raise e

    # QZ0103 修改单个测试
    def put(self, request, id) -> JsonResponse:
        try:
            body = demjson.decode(request.body)
            token = token_pass(request.headers, -1)
            quiz = Quiz.objects.filter(id=id)
            if not quiz.exists():  # 404
                raise QuizNotFoundException()
            quiz = quiz[0]
            body = body["quiz"]
            for key in body:
                setattr(quiz, key, body[key])
            quiz.save()
            return JsonResponse({"quiz": quiz_all(quiz)}, status=200)
        except CommonException as e:  # 500
            raise e

    # QZ0104 删除单个测试
    def delete(self, request, id) -> JsonResponse:
        try:
            quiz = Quiz.objects.filter(id=id)
            token = token_pass(request.headers, -1)
            if not quiz.exists():  # 404
                raise QuizNotFoundException()
            quiz = quiz[0]
            quiz.delete()
            return JsonResponse({}, status=200)
        except CommonException as e:  # 500
            raise e


class MultiQuiz(View):
    # QZ0201 搜索测试题
    def get(self, request) -> JsonResponse:
        try:
            quizzes = Quiz.objects.all()
            # keywords此处默认对question进行模糊搜索
            if "keywords" in request.GET:
                quizzes = quizzes.filter(question__contains=request.GET["keywords"])
            quizzes = list(quizzes)
            result = [quiz_all(quiz) for quiz in quizzes]
            return JsonResponse({"result": result}, status=200)
        except CommonException as e:  # 500
            raise e
        except Exception as e:  # 400
            raise BadRequestException(repr(e))

    # QZ0102 增加单个测试
    def post(self, request) -> JsonResponse:
        body = demjson.decode(request.body)
        token = token_pass(request.headers, -1)
        quiz_form = QuizForm(body)
        if not quiz_form.is_valid():
            raise BadRequestException()
        quiz = quiz_form.save(commit=False)
        quiz.save()
        return JsonResponse({"quiz": quiz_all(quiz)}, status=200)


class RandomQuiz(View):
    # QZ0202 随机测试题
    def get(self, request) -> JsonResponse:
        try:
            quiz = Quiz.objects.order_by("?")[:1]
            if quiz.count() == 0:
                raise QuizNotFoundException()
            else:
                return JsonResponse({"quiz": quiz_all(quiz[0])}, status=200)
        except CommonException as e:  # 500
            raise e
