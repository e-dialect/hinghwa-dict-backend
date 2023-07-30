from ...models import Title


def title_all(title: Title) -> dict:
    response = {
        "name": title.name,
        "points": title.points,
        "id": title.id,
        "color": title.color,
    }
    return response
