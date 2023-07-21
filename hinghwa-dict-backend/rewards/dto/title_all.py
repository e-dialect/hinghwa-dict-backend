from ..models import Title


def title_all(title: Title) -> dict:
    response = {
        "name": title.name,
        "point": title.point,
        "id": title.id,
        "color": title.color,
        "owned": title.owned,
    }

    return response
