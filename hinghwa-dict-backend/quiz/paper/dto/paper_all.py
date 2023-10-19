from ...models import Quiz, Paper, Record
from .record_all import record_all
from quiz.dto.quiz_all import quiz_all


# 返回问卷信息
def paper_all(paper: Paper):
    response = {
        "id": paper.id,
        "title": paper.title,
        "quantity": paper.quantity,
        # "record": [record_all(x) for x in paper.record.all()]
        "quizzes": [quiz_all(quiz) for quiz in paper.quizzes.all()],
    }

    return response
