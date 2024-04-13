# 用于application_all
import json

from ...models import Application


def application_all_content(application: Application) -> dict:
    related_words = [
        {"id": word.id, "word": word.word} for word in application.related_words.all()
    ]
    related_articles = [
        {"id": article.id, "title": article.title}
        for article in application.related_articles.all()
    ]
    tags_list = json.loads(application.tags.replace("'", '"'))
    response = {
        "word": application.content_word,
        "definition": application.definition,
        "annotation": application.annotation,
        "mandarin": eval(application.mandarin) if application.mandarin else [],
        "related_words": related_words,
        "related_articles": related_articles,
        "standard_ipa": application.standard_ipa,
        "standard_pinyin": application.standard_pinyin,
        "tags": tags_list,
    }
    return response
