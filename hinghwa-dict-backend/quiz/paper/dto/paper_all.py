from ...models import Quiz, Paper
from quiz.dto.quiz_all import quiz_all


# 返回问卷信息
def paper_all(paper: Paper):
    response = {
        "id": paper.id,
        "title": paper.title,
        "quizzes": [quiz_all(quiz) for quiz in paper.quizzes.all()],
    }

    return response
