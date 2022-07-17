# 用于WD0402
from ..models import Application
from word.dto.application_all_content import application_all_content
from user.dto.user_simple import user_simple


def application_all(application: Application) -> dict:
    response = {
        "content": application_all_content(application),
        "word": application.word.id if application.word else 0,
        "reason": application.reason,
        "application": application.id,
        "contributor": user_simple(application.contributor),
        "granted": application.granted(),
        "verifier": user_simple(application.verifier) if application.verifier else None,
    }
    return response
