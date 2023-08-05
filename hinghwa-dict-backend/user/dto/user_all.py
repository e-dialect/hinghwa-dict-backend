from ..models import User
from django.utils.timezone import localtime
from utils.Rewards_action import calculate_title, calculate_level


# 返回用户除了 密码 以外的全部信息
def user_all(user: User) -> dict:
    # 获取用户信息
    info = user.user_info
    response = {
        "id": user.id,
        "username": user.username,
        "nickname": info.nickname,
        "email": user.email,
        "telephone": info.telephone,
        "registration_time": localtime(user.date_joined).__format__(
            "%Y-%m-%d %H:%M:%S"
        ),
        "birthday": info.birthday,
        "avatar": info.avatar,
        "county": info.county,
        "town": info.town,
        "is_admin": user.is_superuser,
        "wechat": True if len(info.wechat) else False,
        "points_sum": info.points_sum,
        "points_now": info.points_now,
        "title": calculate_title(info.points_sum),
        "level": calculate_level(info.points_sum),
    }

    response.update(
        {
            "login_time": localtime(user.last_login).__format__("%Y-%m-%d %H:%M:%S")
            if user.last_login
            else "",
        }
    )
    return response
