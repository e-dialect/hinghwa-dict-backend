from ..models import Music

def music_normal(music: Music)->dict:
    response={
        "id": music.id,
        "source": music.source,
        "title": music.title,
        "artist": music.artist,
        "cover": music.cover,
        "likes": music.like(),
        "contributor": music.contributor.id, 
        "visibility": music.visibility
    }
    return response