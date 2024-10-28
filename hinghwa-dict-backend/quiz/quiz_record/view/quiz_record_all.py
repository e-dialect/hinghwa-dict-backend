from django.http import JsonResponse
import demjson3
from ..dto.quiz_record import quiz_record
from django.views import View
from ...models import Quiz, Paper, QuizRecord
from utils.token import token_pass, token_user
from utils.generate_id import generate_quiz_record_id
from ...forms import QuizRecordForm
from utils.exception.types.not_found import (
    PaperRecordNotFoundException,
    QuizNotFoundException,
    UserNotFoundException,
)
from utils.exception.types.bad_request import BadRequestException
from django.utils import timezone
from user.models import User
from ...models import PaperRecord


class QuizRecordAll(View):
    # QZ0401创建答题记录
    def post(self, request):
        token_pass(request.headers)
        body = demjson3.decode(request.body)
        record_form = QuizRecordForm(body)
        quiz_id = request.GET["quiz_id"]
        quiz = Quiz.objects.filter(id=quiz_id)
        if body["paper_record"] != "":
            paper = PaperRecord.objects.filter(id=body["paper_record"])
            if not paper.exists():
                raise PaperRecordNotFoundException()
        if not quiz.exists():
            raise QuizNotFoundException()
        quiz = quiz[0]
        contributor = User.objects.filter(id=body["contributor"])
        if not contributor.exists():
            raise UserNotFoundException()
        contributor = contributor[0]
        if not record_form.is_valid():
            raise BadRequestException()
        record = record_form.save(commit=False)
        record.id = generate_quiz_record_id()
        if body["paper_record"] != "":
            paper = PaperRecord.objects.filter(id=body["paper_record"])
            if not paper.exists():
                raise PaperRecordNotFoundException()
            paper = paper[0]
            record.paper = paper
        record.quiz = quiz
        record.contributor = contributor
        record.timestamp = timezone.now()
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
