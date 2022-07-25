from word.models import Pronunciation


# 语音的基本信息
def pronunciation_simple(item: Pronunciation) -> dict:
    return {
        "word": {"id": item.word.id, "word": item.word.word},
        "source": item.source,
        "ipa": item.ipa,
        "pinyin": item.pinyin,
        "county": item.county,
        "town": item.town,
        "visibility": item.visibility,
    }
