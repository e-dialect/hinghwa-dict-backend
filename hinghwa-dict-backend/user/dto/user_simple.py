from ..models import User


# 返回用户最简单的信息
def user_simple(user: User) -> dict:
    # 获取用户信息
    info = user.user_info
    response = {
        "id": user.id,
        'nickname': info.nickname,
        'avatar': info.avatar,   
    }
    return response