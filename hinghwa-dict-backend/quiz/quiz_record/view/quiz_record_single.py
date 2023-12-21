from django.http import JsonResponse
import demjson
from ..dto.quiz_record import quiz_record
from django.views import View
from ...models import Paper, QuizRecord, PaperRecord
from utils.token import token_pass
from ...forms import QuizRecordForm
from utils.exception.types.not_found import (
    UserNotFoundException,
    PaperRecordNotFoundException,
    QuizRecordNotFoundException,
)
from django.utils import timezone
from user.models import User


class QuizRecordSingle(View):
    # QZ0403查询特定答题记录
    def get(self, request, record_id):
        token_pass(request.headers, -1)
        record = QuizRecord.objects.filter(id=record_id)
        if not record.exists():
            raise QuizRecordNotFoundException
        record = record[0]
        return JsonResponse(quiz_record(record), status=200)

    # QZ0404更改特定答题记录
    def put(self, request, record_id):
        token_pass(request.headers, -1)
        body = demjson.decode(request.body)
        if body["paper_record"] != "":
            paper = PaperRecord.objects.filter(id=body["paper_record"])
            if not paper.exists():
                raise PaperRecordNotFoundException()
        record = QuizRecord.objects.filter(id=record_id)
        if not record.exists():
            raise QuizRecordNotFoundException
        record = record[0]
        record.answer = body["answer"]
        record.correctness = body["correctness"]
        contributor = User.objects.filter(id=body["contributor"])
        if not contributor.exists():
            raise UserNotFoundException()
        contributor = contributor[0]
        if body["paper_record"] != "":
            paper = PaperRecord.objects.filter(id=body["paper_record"])
            if not paper.exists():
                raise PaperRecordNotFoundException()
            paper = paper[0]
            record.paper = paper
        record.timestamp = timezone.now()
        record.contributor = contributor
        record.save()
        return JsonResponse(quiz_record(record), status=200)

    # QZ0405删除特定答题记录
    def delete(self, request, record_id):
        token_pass(request.headers, -1)
        record = QuizRecord.objects.filter(id=record_id)
        id = str(record_id)
        if not record.exists():
            raise QuizRecordNotFoundException
        record = record[0]
        record.delete()
        return JsonResponse({"msg": "答题记录{}删除成功".format(id)}, status=200)
