from ...models import QuizRecord
from ...dto.quiz_all import quiz_all
from ...paper.dto.paper_simple import paper_simple


def quiz_record(record: QuizRecord):
    response = {
        "id": record.id,
        "quiz": quiz_all(record.quiz),
        "answer": record.answer,
        "correctness": record.correctness,
        "paper": None if record.paper is None else paper_simple(record.paper)
    }

    return response
