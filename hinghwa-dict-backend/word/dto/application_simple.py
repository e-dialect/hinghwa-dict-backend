# 用于WD0403
from ..models import Application
from word.dto.application_simple_content import application_simple_content
from user.dto.user_simple import user_simple


def application_simple(application: Application) -> dict:

    response = {
        "content": application_simple_content(application),
        "word": application.word.id if application.word else 0,
        "reason": application.reason,
        "application": application.id,
        "contributor": user_simple(application.contributor),
        "granted": application.granted(),
        "verifier": user_simple(application.verifier) if application.verifier else None,
    }
    return response
