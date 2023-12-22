from ...models import QuizRecord
from ...dto.quiz_all import quiz_all
from ...paper.dto.paper_record_dto import paper_record_all
from user.dto.user_simple import user_simple


def quiz_record(record: QuizRecord):
    response = {
        "id": record.id,
        "contributor": user_simple(record.contributor),
        "timestamp": record.timestamp,
        "quiz": quiz_all(record.quiz),
        "answer": record.answer,
        "correctness": record.correctness,
        "paper": None if record.paper is None else paper_record_all(record.paper),
    }

    return response
