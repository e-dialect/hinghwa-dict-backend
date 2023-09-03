from ...models import List
from ...word.dto.word_simple import word_simple
from user.dto.user_simple import user_simple


def list_all(list: List):
    response = {
        "name": list.name,
        "author": user_simple(list.author),
        "createTime": list.createTime,
        "updateTime": list.updateTime,
        "description": list.description,
        "words": [word_simple(x) for x in list.words.all()],
        "length": list.words.count(),
        "id": list.id,
    }

    return response
