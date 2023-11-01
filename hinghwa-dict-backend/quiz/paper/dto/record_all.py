from ...models import Record
from user.dto.user_simple import user_simple
from .paper_all import paper_all


def record_all(record: Record):
    response = {
        "timestamp": record.timestamp,
        "correct_answer": record.correct_answer,
        "answer_user": user_simple(record.answer_user),
        "paper": paper_all(record.exam)
    }
    return response
