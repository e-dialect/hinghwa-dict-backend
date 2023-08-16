from django.http import JsonResponse
from ..dto.transactions_all import transactions_all
from ..models.transaction import Transaction
from django.views import View
from user.utils import get_user_by_id
from datetime import datetime
from django.core.paginator import Paginator


class SearchFromUser(View):
    # RE0302查询交易记录
    def get(self, request):
        user_id = request.GET["user"]
        page = request.GET.get("page", 1)
        pageSize = request.GET.get("pageSize", 10)
        if not page:
            page = 1
        if not pageSize:
            pageSize = 10
        action = request.GET["action"]
        start_time = request.GET["start_date"]
        end_time = request.GET["end_date"]
        filters = {}
        amount = 0
        results = []
        if action:
            filters["action"] = action
        if start_time:
            start_time = datetime.strptime(start_time, "%Y-%m-%d")
            filters["timestamp__gte"] = start_time
        if end_time:
            end_time = datetime.strptime(end_time, "%Y-%m-%d")
            filters["timestamp__lte"] = end_time
        filters["user"] = user_id
        transactions_result = Transaction.objects.filter(**filters)
        # TODO 真正实现筛选功能
        for transaction in transactions_result:
            results.append(transactions_all(transaction))
            amount += 1
        paginator = Paginator(transactions_result, pageSize)
        current_page = paginator.get_page(page)
        return JsonResponse(
            {
                "results": results,
                "amount": str(amount),
                "total_pages": str(paginator.num_pages),
                "page": str(current_page.number),
                "pageSize": str(pageSize),
            }
        )
