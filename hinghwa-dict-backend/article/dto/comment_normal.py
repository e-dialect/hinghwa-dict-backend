from ..models import Comment
from user.dto.user_simple import user_simple


# 返回评论基本信息
def comment_normal(comment: Comment) -> dict:
    user = comment.user
    response = {
        "id": comment.id,
        "user": user_simple(user),
        "content": comment.content,
        "time": comment.time.__format__("%Y-%m-%d %H:%M:%S"),
        "parent": comment.parent_id if comment.parent else 0,
        "article": comment.article.id,
    }
    return response
