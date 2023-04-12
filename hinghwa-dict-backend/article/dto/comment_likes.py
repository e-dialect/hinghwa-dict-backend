from user.dto.user_simple import user_simple
from ..models import Comment


# 返回评论点赞信息
def comment_likes(comment: Comment) -> dict:
    res_num = 5  # 指的是返回的点赞的用户个数
    # 找到对应的评论
    comment_like_users = comment.like_users.filter(like_comments=comment)
    user_list = []
    for one_user in comment_like_users[0:res_num]:
        user_list.append(user_simple(one_user))
    response = {
        "id": comment.id,
        "likes": comment.like(),
        "like_users": user_list,
    }
    return response
