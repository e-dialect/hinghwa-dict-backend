from ..models import Comment


# 返回评论基本信息
def comment_normal(comment: Comment) -> dict:
    response = {
        "id": comment.id,
        "user": comment.user.id,
        "content": comment.content,
        "time": comment.time.__format__("%Y-%m-%d %H:%M:%S"),
        "parent": comment.parent_id if comment.parent else 0,
        "article": comment.article.id,
    }
    return response
