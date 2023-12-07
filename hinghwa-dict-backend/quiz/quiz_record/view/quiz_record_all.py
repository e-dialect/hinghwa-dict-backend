from django.http import JsonResponse
import demjson
from ..dto.quiz_record import quiz_record
from django.views import View
from ...models import Quiz, Paper, QuizRecord
from utils.token import token_pass, token_user
from utils.generate_id import generate_quiz_record_id
from ...forms import QuizRecordForm
from utils.exception.types.not_found import (
    PaperNotFoundException,
    QuizNotFoundException,
)
from utils.exception.types.bad_request import BadRequestException


class QuizRecordAll(View):
    # QZ0401创建答题记录
    def post(self, request):
        token_pass(request.headers)
        body = demjson.decode(request.body)
        record_form = QuizRecordForm(body)
        quiz_id = request.GET["quiz_id"]
        quiz = Quiz.objects.filter(id=quiz_id)
        if body["paper"] != "":
            paper = Paper.objects.filter(id=body["paper"])
            if not paper.exists():
                raise PaperNotFoundException()
        if not quiz.exists():
            raise QuizNotFoundException()
        quiz = quiz[0]
        if not record_form.is_valid():
            raise BadRequestException()
        record = record_form.save(commit=False)
        record.id = generate_quiz_record_id()
        print()
        if body["paper"] != "":
            paper = Paper.objects.filter(id=body["paper"])
            if not paper.exists():
                raise PaperNotFoundException()
            paper = paper[0]
            record.paper = paper
        record.quiz = quiz
        record.save()
        return JsonResponse(quiz_record(record), status=200)

    # QZ0402查询所有答题记录
    def get(self, request):
        token_pass(request.headers, -1)
        records = QuizRecord.objects.all()
        results = []
        for record in records:
            results.append(quiz_record(record))
        return JsonResponse({"total": len(results), "records": results}, status=200)
