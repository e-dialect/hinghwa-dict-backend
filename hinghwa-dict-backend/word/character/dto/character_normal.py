from ...models import Character


def character_normal(character: Character) -> dict:
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
    }
    return response
