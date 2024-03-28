# 用于WD0202
import json

from ...models import Word


def word_simple(word: Word) -> dict:
    user = word.contributor
    tags_list = json.loads(word.tags.replace("'", '"'))
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
        "tags": tags_list,
    }
    return response
