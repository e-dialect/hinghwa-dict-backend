from urllib import response
from ..models import Word


def word_normal(word: Word) -> dict:
    related_words = [
        {"id": word.id, "word": word.word} for word in word.related_words.all()
    ]
    related_articles = [
        {"id": article.id, "title": article.title}
        for article in word.related_articles.all()
    ]
    response = {
        "word": word.word,
        "definition": word.definition,
        "annotation": word.annotation,
        "mandarin": eval(word.mandarin) if word.mandarin else [],
        "related_words": related_words,
        "related_articles": related_articles,
        "standard_ipa": word.standard_ipa,
        "standard_pinyin": word.standard_pinyin,
    }
