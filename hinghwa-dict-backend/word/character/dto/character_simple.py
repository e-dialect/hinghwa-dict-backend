from ...models import Character, Word, Pronunciation


def character_simple(character: Character) -> dict:
    dic = {}
    word = Word.objects.filter(standard_pinyin=character.pinyin).filter(
        word=character.character
    )
    word_id = word[0].id if word.exists() else None
    source = Pronunciation.objects.filter(pinyin=character.pinyin)
    source_value = source[0].source if source.exists() else None

    # 构建字典
    key = (character.character, character.traditional)
    if key not in dic:
        dic[key] = []

    dic[key].append(
        {
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
            "word": {"id": word_id} if word else None,
            "source": {"source": source_value} if source else None,
            "type": None if character.type is None else character.type,
        }
    )

    ans = []
    for key, value in dic.items():
        char, traditional = key
        result_list = [
            {"county": item["county"], "town": item["town"], "characters": item}
            for item in value
        ]
        ans.append(
            {
                "label": char,
                "traditional": traditional,
                "characters": result_list,
            }
        )
    ans = ans[0]

    return ans
