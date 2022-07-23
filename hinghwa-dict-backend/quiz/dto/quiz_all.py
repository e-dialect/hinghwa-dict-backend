from ..models import Quiz


def quiz_all(quiz: Quiz) -> dict:
    # 获取测试问题信息
    response = {
        "id": quiz.id,
        "question": quiz.question,
        "options": eval(quiz.options) if quiz.options else [],
        "explanation": quiz.explanation,
    }
    return response
