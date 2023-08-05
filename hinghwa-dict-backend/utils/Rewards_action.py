import uuid
from user.models import User, UserInfo
from rewards.transactions.models.transaction import Transaction
from utils.exception.types.not_found import UserNotFoundException
from utils.exception.types.bad_request import BadRequestException
from rewards.transactions.models.transaction import Transaction
from django.utils import timezone
from .generate_id import generate_transaction_id
from rewards.transactions.dto.transactions_all import transactions_all


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


def calculate_level(points_sum):
    if 0 <= points_sum < 100:
        return 1
    elif points_sum < 500:
        return 2
    elif points_sum < 1000:
        return 3
    elif points_sum < 2000:
        return 4
    elif points_sum < 5000:
        return 5
    else:
        return 6


def points_change(action, points, user_id):
    user = User.objects.filter(id=user_id)
    if user.exists():
        user = user[0]
        if action == "earn":
            user.user_info.points_sum += points
            user.user_info.points_now += points
        elif action == "redeem":
            if user.user_info.points_now >= points:
                user.user_info.points_now -= points
            else:
                raise BadRequestException("积分不足")
        else:
            raise BadRequestException("action错误")
        user.user_info.save()
    else:
        raise UserNotFoundException()


def create_transaction(action, points, reason, user_id):
    user = User.objects.filter(id=user_id)
    if user.exists():
        user = user[0]
        transaction = Transaction()
        transaction.action = action
        transaction.points = points
        transaction.reason = reason
        transaction.user = user
        transaction.timestamp = timezone.now()
        transaction.id = generate_transaction_id()
        transaction.save()
        return transactions_all(transaction)
    else:
        raise UserNotFoundException()


def manage_points_in_article(user_id):
    action = "earn"
    points = 50
    reason = "贡献文章"
    transaction_info = create_transaction(
        action=action, points=points, reason=reason, user_id=user_id
    )
    points_change(action=action, points=points, user_id=user_id)

    return transaction_info


def manage_points_in_quiz(user_id):
    action = "earn"
    points = 30
    reason = "贡献题库"
    transaction_info = create_transaction(
        action=action, points=points, reason=reason, user_id=user_id
    )
    points_change(action=action, points=points, user_id=user_id)
    return transaction_info


def manage_points_in_pronunciation(user_id):
    action = "earn"
    points = 30
    reason = "贡献语音"
    transaction_info = create_transaction(
        action=action, points=points, reason=reason, user_id=user_id
    )
    points_change(action=action, points=points, user_id=user_id)
    return transaction_info
