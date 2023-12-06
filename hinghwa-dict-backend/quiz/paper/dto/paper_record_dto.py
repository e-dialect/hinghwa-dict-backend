from ...models import Quiz, Paper, PaperRecord
from quiz.dto.quiz_all import quiz_all
from user.dto.user_simple import user_simple
from .paper_all import paper_all


def paper_record_all(paper_record: PaperRecord):
    response = {
        "id": paper_record.id,
        "user": user_simple(paper_record.contributor),
        "timestamp": paper_record.timestamp,
        "paper": paper_all(paper_record.paper),
    }

    return response
