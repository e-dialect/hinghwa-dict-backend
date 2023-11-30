from django.http import JsonResponse
from ..dto.paper_record_dto import paper_record_all
from django.views import View
from utils.token import token_pass
from utils.exception.types.not_found import PaperRecordNotFoundException
from ...models import PaperRecord


class PaperRecordSingle(View):
    # QZ0303 查询单个答卷记录
    def get(self, request, record_id):
        record = PaperRecord.objects.filter(id=record_id)
        if not record.exists():
            raise PaperRecordNotFoundException()
        record = record[0]
        user_id = record.examine.id
        token_pass(request.headers, user_id)
        return JsonResponse(paper_record_all(record), status=200)
