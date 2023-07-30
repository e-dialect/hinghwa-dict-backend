import uuid
from user.models import User, UserInfo
from rewards.models import Transactions
from utils.exception.types.not_found import UserNotFoundException
from utils.exception.types.bad_request import BadRequestException
from rewards.models import Transactions
from django.utils import timezone
from .generate_id import generate_transaction_id


def calculate_title(points_sum) -> dict:
    """
    称号和积分折合等级，暂定颜色由前端决定吧
    :param points_sum: 总积分
    """
    if 0 <= points_sum < 200:
        title = "语言小白"
        color = "#00FF00"
    elif 200 <= points_sum < 500:
        title = "语言学者"
        color = "#FF0000"
    else:
        title = "语言大师"
        color = "#FF00FF"

    response = {"title": title, "color": color}

    return response


def points_change(action, points, user_id):
    user = User.objects.filter(id=user_id)
    if user.exists():
        user = user[0]
        if action == "add":
            user.user_info.points_sum += points
            user.user_info.points_now += points
        elif action == "sub":
            if user.user_info.points_now >= points:
                user.user_info.points_now -= points
        else:
            return BadRequestException
        user.user_info.save()
    else:
        raise UserNotFoundException()


def create_transaction(action, points, reason, user_id):
    user = User.objects.filter(id=user_id)
    if user.exists():
        user = user[0]
        transaction = Transactions()
        transaction.action = action
        transaction.points = points
        transaction.reason = reason
        transaction.user = user
        transaction.timestamp = timezone.now()
        transaction.id = generate_transaction_id()
        transaction.save()
        return transaction.id
    else:
        raise UserNotFoundException()
