from word.models import Pronunciation
from user.dto.user_all import user_all


# 返回语音的所有信息
def pronunciation_all(pronunciation: Pronunciation) -> dict:
    user = pronunciation.contributor
    response = {
        "id": pronunciation.id,
        "word_id": pronunciation.word.id,
        "word_word": pronunciation.word.word,
        "source": pronunciation.source,
        "ipa": pronunciation.ipa,
        "pinyin": pronunciation.pinyin,
        "contributor": user_all(user),
        "county": pronunciation.county,
        "town": pronunciation.town,
        "visibility": pronunciation.visibility,
        "verifier": {
            "nickname": pronunciation.verifier.user_info.nickname,
            "avatar": pronunciation.verifier.user_info.avatar,
            "id": pronunciation.verifier.id,
        }
        if pronunciation.verifier
        else None,
        "granted": pronunciation.granted(),
        "upload_time": pronunciation.upload_time.__format__("%Y-%m-%d %H:%M:%S"),
    }
    return response
