import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..dto.transactions_all import transactions_all
from utils.exception.types.not_found import TransactionsNotFoundException
from django.conf import settings
from ...models import Transactions
from ..forms import TransactionsInfoForm
from django.views import View
from utils.exception.types.bad_request import BadRequestException
from utils.token import token_pass


class SearchFromID(View):
    # RE0301查询特定交易记录
    def get(self, request, transaction_id):
        transaction = Transactions.objects.filter(id=transaction_id)
        if not transaction.exists():
            raise TransactionsNotFoundException()
        transaction = transaction[0]
        return JsonResponse({"transaction": transactions_all(transaction)})
