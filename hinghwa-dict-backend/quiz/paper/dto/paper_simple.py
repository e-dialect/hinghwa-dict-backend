from ...models import Paper


# 返回问卷简单信息
def paper_simple(paper: Paper):
    response = {
        "id": paper.id,
        "title": paper.title,
    }

    return response
