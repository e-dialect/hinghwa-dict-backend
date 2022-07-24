# 用于WD0202
from ...models import Word


def word_simple(word: Word) -> dict:
    user = Word.contributor
    response = {
        "id": word.id,
        "word": word.word,
        "definition": word.definition,
        "contributor": user.id,
        "annotation": word.annotation,
        "mandarin": eval(word.mandarin) if word.mandarin else [],
        "views": word.views,
        "standard_ipa": word.standard_ipa,
        "standard_pinyin": word.standard_pinyin,
    }
    return response
