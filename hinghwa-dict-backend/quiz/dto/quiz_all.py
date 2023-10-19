from ..models import Quiz
from user.dto.user_all import user_all


def quiz_all(quiz: Quiz) -> dict:
    # 获取测试问题信息
    user = quiz.author
    response = {
        "id": quiz.id,
        "author": user_all(user),
        "question": quiz.question,
        "options": eval(quiz.options) if quiz.options else [],
        "answer": quiz.answer,
        "explanation": quiz.explanation,
        "voice_source": quiz.voice_source,
        "visibility": quiz.visibility,
        "type": quiz.type,
    }
    return response
