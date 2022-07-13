from ..models import Music


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
        "contributor": {
            "id": user.id,
            'username': user.username,
            'nickname': music.contributor.user_info.nickname,
            'email': user.email,
            'telephone': user.user_info.telephone,
            'registration_time':
            user.date_joined.__format__('%Y-%m-%d %H:%M:%S'),
            'birthday': user.user_info.birthday,
            'avatar': user.user_info.avatar,
            'county': user.user_info.county,
            'town': user.user_info.town,
            'is_admin': user.is_superuser
        },
        "visibility": music.visibility
    }
    response.update({
        'login_time':
        user.last_login.__format__('%Y-%m-%d %H:%M:%S')
        if user.last_login else '',
    })
    return response
