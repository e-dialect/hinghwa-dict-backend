# 可用于WD0101
from ..models import Word
from user.dto.user_simple import user_simple
from word.word import word2pronunciation


def word_all(word: Word) -> dict:
    related_words = [
        {"id": word.id, "word": word.word} for word in word.related_words.all()
    ]
    related_articles = [
        {"id": article.id, "title": article.title}
        for article in word.related_articles.all()
    ]
    user = word.contributor
    source = word2pronunciation(word)
    response = {
        "id": word.id,
        "word": word.word,
        "definition": word.definition,
        "contributor": user_simple(user),
        "annotation": word.annotation,
        "standard_ipa": word.standard_ipa,
        "standard_pinyin": word.standard_pinyin,
        "mandarin": eval(word.mandarin) if word.mandarin else [],
        "related_words": related_words,
        "related_articles": related_articles,
        "views": word.views,
        "source": source,
    }
    return response
