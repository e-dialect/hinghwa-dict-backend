from django.http import JsonResponse
from ..dto.transactions_all import transactions_all
from utils.exception.types.not_found import TransactionsNotFoundException
from ..models.transaction import Transaction
from django.views import View


class SearchFromID(View):
    # RE0301查询特定交易记录
    def get(self, request, transaction_id):
        transaction = Transaction.objects.filter(id=transaction_id)
        if not transaction.exists():
            raise TransactionsNotFoundException()
        transaction = transaction[0]
        return JsonResponse({"transaction": transactions_all(transaction)})
