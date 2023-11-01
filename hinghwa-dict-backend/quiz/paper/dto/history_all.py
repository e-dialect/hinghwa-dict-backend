from ...models import QuizHistory
from .paper_all import paper_all


def quiz_history_all(history: QuizHistory):
    response = {
       "id": history.id,
       "total": history.total,
       "papers": [paper_all(paper) for paper in history.paper]
    }
    return response
