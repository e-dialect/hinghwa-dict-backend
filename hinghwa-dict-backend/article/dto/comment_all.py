from ..models import Comment
from user.dto.user_simple import user_simple
from django.utils.timezone import localtime
from .comment_normal import comment_normal


# 返回评论基本信息
def comment_all(comment: Comment, res_num=None) -> dict:
    if res_num is None:
        res_num = 5
    user = comment.user
    comment_like_users = comment.like_users.filter()
    user_list = []
    for one_user in comment_like_users[0:res_num]:
        user_list.append(user_simple(one_user))
    children = Comment.objects.filter(parent_id=comment.id)
    children_list = []
    for one_comment in children:
        children_list.append(comment_normal(one_comment))

    response = {
        "id": comment.id,
        "user": user_simple(user),
        "content": comment.content,
        "time": localtime(comment.time).__format__("%Y-%m-%d %H:%M:%S"),
        "parent": comment.parent_id if comment.parent else 0,
        "children": children_list,
        "article": comment.article.id,
        "likes": comment.like(),
        "like_users": user_list,
    }
    return response
