from word.models import Pronunciation


# 返回语音的一般信息
def pronunciation_normal(pronunciation: Pronunciation) -> dict:
    response = {
        "id": pronunciation.id,
        "word_id": pronunciation.word.id,
        "word_word": pronunciation.word.word,
        "source": pronunciation.source,
        "ipa": pronunciation.ipa,
        "pinyin": pronunciation.pinyin,
        "contributor": pronunciation.contributor.id,
        "county": pronunciation.county,
        "town": pronunciation.town,
        "visibility": pronunciation.visibility,
        "verifier": (
            {
                "nickname": pronunciation.verifier.user_info.nickname,
                "avatar": pronunciation.verifier.user_info.avatar,
                "id": pronunciation.verifier.id,
            }
            if pronunciation.verifier
            else None
        ),
        "granted": pronunciation.granted(),
    }
    return response
