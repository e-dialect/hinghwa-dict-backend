from django.http import JsonResponse
import demjson
from ..dto.paper_all import paper_all
from ..dto.record_all import record_all
from ..dto.history_all import quiz_history_all
from django.views import View
from user.models import User
from django.views.decorators.csrf import csrf_exempt
from ...models import Quiz, Paper, Record, QuizHistory
from utils.exception.types.bad_request import InsufficientQuiz
from utils.token import token_pass, token_user
from django.utils import timezone


# 这个作为功能函数到时候直接在创建quiz时调用
def create_quiz_history(id):
    history = QuizHistory()
    history.id = id
    history.total = 0
    history.save()

class QuizHistory(View):
    # 查询
    def get(self, request):
        token_pass(request.headers, -1)
        history_id = request.GET["request_id"]
        history = QuizHistory.objects.filter(id=history_id)
        return JsonResponse(quiz_history_all(history))
