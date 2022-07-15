# 用于WD0201
from urllib import response
from ..models import Word


def word_quick(word: Word) -> dict:
    response = {
        "id": word.id,
        "word": word.word,
        "definition": word.definition,
        "annotation": word.annotation,
        "mandarin": eval(word.mandarin) if word.mandarin else [],
        "standard_ipa": word.standard_ipa,
        "standard_pinyin": word.standard_pinyin,
    }
    return response
