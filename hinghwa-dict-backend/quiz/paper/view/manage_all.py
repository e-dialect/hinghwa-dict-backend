from django.http import JsonResponse
import demjson
from ..dto.paper_all import paper_all
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from ...models import Quiz, Paper, Record
from utils.exception.types.bad_request import InsufficientQuiz
from utils.token import token_pass, token_user
from django.utils import timezone
from utils.generate_id import generate_paper_id


class ManageAllPaper(View):
    # QZ0203 测试题组卷
    @csrf_exempt
    def post(self, request):
        token_pass(request.headers, -1)
        number = int(request.GET["number"])
        body = demjson.decode(request.body)
        title = body["title"]
        request_type = request.GET["type"]
        type_list = request_type.split(",")
        quizzes = Quiz.objects.filter(type__in=type_list).order_by("?")[:number]
        if len(quizzes) != number:
            raise InsufficientQuiz()
        paper = Paper()
        paper.quantity = number
        paper.id = generate_paper_id()
        paper.title = title
        paper.save()
        for quiz in quizzes:
            paper.quizzes.add(quiz)
        return JsonResponse(paper_all(paper), status=200)

    # QZ0204 查询所有试卷
    @csrf_exempt
    def get(self, request):
        # token_pass(request.headers, -1)
        total_papers = Paper.objects.all()
        result = []
        for paper in total_papers:
            result.append(paper_all(paper))
        return JsonResponse({"total": len(result), "paper": result})
