from ...models import Character
from ...models import Word
from ...models import Pronunciation


def character_all(character: Character, word: Word, source: Pronunciation) -> dict:
    response = {
        "id": character.id,
        "shengmu": character.shengmu,
        "ipa": character.ipa,
        "pinyin": character.pinyin,
        "yunmu": character.yunmu,
        "shengdiao": character.shengdiao,
        "character": character.character,
        "county": character.county,
        "town": character.town,
        "traditional": character.traditional,
        "word": word,
        "source": source,
        "type": None if character.type is None else character.type,
    }
    return response
