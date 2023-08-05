from django.http import JsonResponse
from ..dto.transactions_all import transactions_all
from ..models.transaction import Transaction
from django.views import View
from user.utils import get_user_by_id


class SearchFromUser(View):
    # RE0302查询交易记录
    def get(self, request):
        user_id = request.GET["user"]
        page = request.GET.get("page", 1)
        pageSize = request.GET.get("pageSize", 10)
        action = request.GET["action"]
        amount = 0
        results = []
        transactions = Transaction.objects.filter(user=get_user_by_id(user_id))
        # TODO 真正实现筛选功能
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
