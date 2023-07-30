from ..models import User
from django.utils.timezone import localtime
from utils.Rewards_action import calculate_title


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
    }

    response.update(
        {
            "login_time": localtime(user.last_login).__format__("%Y-%m-%d %H:%M:%S")
            if user.last_login
            else "",
        }
    )
    return response


def user_pointts_change(user: User) -> dict:
    # 获取用户积分变动信息
    info = user.user_info
    response = {"points_change": []}
    if info.reasons and info.timestamps:
        reasons_and_timestamps = info.combine()
        points_change = [
            {"reason": info.reasons, "timestamp": info.timestamps}
            for info.reasons, info.timestamps in reasons_and_timestamps
        ]
        response["points_change"] = points_change

    return response
