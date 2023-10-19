import demjson
from django.http import JsonResponse
from ..dto.paper_all import paper_all
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from ...models import Quiz, Paper, Record
from utils.exception.types.bad_request import InsufficientQuiz
from utils.exception.types.not_found import PaperNotFoundException


class ManageSinglePaper(View):
    # QZ0205 查询特定试卷
    @csrf_exempt
    def get(self, request, paper_id) -> JsonResponse:
        paper = Paper.objects.filter(id=paper_id)
        if not paper.exists():
            raise PaperNotFoundException()
        paper = paper[0]
        return JsonResponse(paper_all(paper), status=200)
