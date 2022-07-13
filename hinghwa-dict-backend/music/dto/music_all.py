from ..models import Music
from user.dto.user_all import user_all


def music_all(music: Music) -> dict:
    # 获取音乐信息
    user = music.contributor
    response = {
        "id": music.id,
        "source": music.source,
        "title": music.title,
        "artist": music.artist,
        "cover": music.cover,
        "likes": music.like(),
        "contributor": user_all(user),
        "visibility": music.visibility
    }
    return response
