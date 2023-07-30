import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..dto.transactions_all import transactions_all
from utils.exception.types.not_found import (
    TransactionsNotFoundException,
    UserNotFoundException,
)
from django.conf import settings
from ...models import Transactions
from ..forms import TransactionsInfoForm
from django.views import View
from utils.exception.types.bad_request import BadRequestException
from utils.token import token_pass, token_user
from user.dto.user_simple import user_simple
from user.utils import get_user_by_id
from django.utils import timezone
import random


class SearchFromUser(View):
    # RE0302查询交易记录
    def get(self, request):
        user_id = request.GET["user"]
        page = request.GET.get("page", 1)
        pageSize = request.GET.get("pageSize", 10)
        action = request.GET["action"]
        amount = 0
        results = []
        transactions = Transactions.objects.filter(user=get_user_by_id(user_id))
        for transaction in transactions:
            results.append(transactions_all(transaction))
            amount += 1
        return JsonResponse(
            {
                "results": results,
                "amount": str(amount),
                "page": str(page),
                "pageSize": str(pageSize),
            }
        )
