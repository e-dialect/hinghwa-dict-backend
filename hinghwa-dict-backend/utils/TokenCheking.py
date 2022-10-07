import string
import numbers
import jwt
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from utils.exception.types.forbidden import OnlyAdminException
from utils.exception.types.forbidden import ForbiddenException
from utils.exception.types.unauthorized import (
    InvalidTokenException,
    OutdatedException,
    UnauthorizedException,
)


def token_pass(header: dict, id: numbers = 0) -> string:
    """
    验证token是否合法
    成功满足要求的验证则自动刷新时长，100分钟未操作则自动超时
    :param token: token
    :param id: -1 表示要求管理员权限, 0 表示任意用户都允许通过, x 表示用户id需要为x
    :return: {{token}} 表示通过验证
    """
    # 如果没有token
    if "token" not in header:
        raise UnauthorizedException()

    token = header["token"]
    key = settings.JWT_KEY

    # 如果token无效
    try:
        info = jwt.decode(token, key, algorithms=["HS256"])
    except Exception:
        raise InvalidTokenException()
    if not ("id" in info and "exp" in info and "username" in info):
        raise InvalidTokenException()
    try:
        user = User.objects.get(id=info["id"])
    except User.DoesNotExist:
        raise InvalidTokenException()

    # 如果token过期
    if info["exp"] < timezone.now().timestamp():
        raise OutdatedException()

    # 如果要求管理员权限
    if id == -1 and not user.is_superuser:
        raise OnlyAdminException()

    # 如果要求指定用户
    if id > 0 and user.id != id and not user.is_superuser:
        raise ForbiddenException()

    return token


def token_user(token: string) -> User:
    """
    返回token中的用户
    :param token: token
    :return:
    """
    token_pass({"token": token})
    key = settings.JWT_KEY
    info = jwt.decode(token, key, algorithms=["HS256"])
    user = User.objects.get(id=info["id"])
    return user
