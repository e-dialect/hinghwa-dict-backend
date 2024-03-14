from django.http import JsonResponse
from ..dto.paper_record_dto import paper_record_all
from django.views import View
from ...models import Quiz, Paper
from utils.token import token_pass, token_user
from utils.generate_id import generate_paper_record_id
from user.models import User
from utils.exception.types.bad_request import BadRequestException
from ...models import PaperRecord
from user.utils import get_user_by_id
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt


class PaperRecordAll(View):
    # QZ0301 创建答卷记录
    @csrf_exempt
    def post(self, request):
        token = token_pass(request.headers)
        user = token_user(token)
        token_pass(request.headers, user.id)
        contributor = request.GET["contributor"]
        paper = request.GET["paper"]
        paper = Paper.objects.filter(id=paper)
        paper = paper[0]
        record = PaperRecord()
        record.timestamp = timezone.now()
        record.id = generate_paper_record_id()
        record.contributor = get_user_by_id(contributor)
        record.paper = paper
        record.save()
        return JsonResponse(paper_record_all(record))

    # QZ0302 查询对应用户答卷记录
    def get(self, request):
        user_id = request.GET["user_id"]
        token_pass(request.headers, int(user_id))
        total_records = PaperRecord.objects.filter(contributor=get_user_by_id(user_id))
        results = []
        for record in total_records:
            results.append(paper_record_all(record))
        return JsonResponse({"total": len(results), "records": results})
