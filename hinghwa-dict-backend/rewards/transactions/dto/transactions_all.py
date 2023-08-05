from ..models.transaction import Transaction
from user.dto.user_simple import user_simple


def transactions_all(transactions: Transaction) -> dict:
    response = {
        "user": user_simple(transactions.user),
        "timestamp": transactions.timestamp,
        "action": transactions.action,
        "points": transactions.points,
        "id": transactions.id,
        "reason": transactions.reason,
    }

    return response
