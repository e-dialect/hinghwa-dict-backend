# 用于application_simple
import json

from ...models import Application


def application_simple_content(application: Application) -> dict:
    # Handle empty or malformed tags field
    try:
        if not application.tags or not application.tags.strip():
            tags_list = []
        else:
            tags_list = json.loads(application.tags.replace("'", '"'))
    except (json.JSONDecodeError, ValueError):
        tags_list = []

    response = {
        "word": application.content_word,
        "definition": application.definition,
        "annotation": application.annotation,
        "standard_ipa": application.standard_ipa,
        "standard_pinyin": application.standard_pinyin,
        "mandarin": eval(application.mandarin) if application.mandarin else [],
        "tags": tags_list,
    }
    return response
