# 用于application_simple
from ...models import Application


def application_simple_content(application: Application) -> dict:
    response = {
        "word": application.content_word,
        "definition": application.definition,
        "annotation": application.annotation,
        "standard_ipa": application.standard_ipa,
        "standard_pinyin": application.standard_pinyin,
        "mandarin": eval(application.mandarin) if application.mandarin else [],
    }
    return response
