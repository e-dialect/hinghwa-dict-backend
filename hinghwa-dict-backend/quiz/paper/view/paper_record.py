from django.http import JsonResponse
import demjson
from ..dto.paper_all import paper_all
from ..dto.record_all import record_all
from django.views import View
from user.models import User
from django.views.decorators.csrf import csrf_exempt
from ...models import Quiz, Paper, Record, QuizHistory
from utils.exception.types.bad_request import InsufficientQuiz
from utils.token import token_pass, token_user
from django.utils import timezone
from utils.generate_id import generate_paper_record_id


class PaperRecord(View):
    # 创建答题记录
    def post(self, request):
        token_pass(request.headers, -1)
        body = demjson.decode(request.body)
        answer_user = body["answer_user"]
        correct_answer = body["correct_answer"]
        paper_id = body["paper"]
        user = User.objects.filter(id=answer_user)
        paper = Paper.objects.filter(id=paper_id)
        record = Record()
        record.correct_answer = correct_answer
        record.id = generate_paper_record_id()
        record.timestamp = timezone.now()
        record.answer_user = user
        record.save()
        record.exam.add(paper)
        quizzes = paper.quizzes.all()
        for quiz in quizzes:
            history = QuizHistory.objects.filter(id=quiz.id)
            history.total += 1
            history.paper.add(paper)
        return JsonResponse(record_all(record))

    # 查询所有答题记录
    def get(self, request):
        user = request.GET["user_id"]
        token_pass(request.headers, user)
        total_records = Record.objects.filter(answer_user__id=user)
        results = []
        for record in total_records:
            results.append(record_all(record))
        return JsonResponse({"total": len(results), "record": results})
