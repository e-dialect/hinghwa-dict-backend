import datetime
import string
import numbers
import jwt
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.utils import timezone
from django.http import request
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


def generate_token(user: User) -> string:
    """
    生成token
    :param user: 用户
    :return: token
    """
    payload = {
        "username": user.username,
        "id": user.id,
        "exp": (timezone.now() + datetime.timedelta(days=7)).timestamp(),
    }
    # 不知道为什么，本地显示jwt.encode是Object但是服务器显示是str
    token = jwt.encode(payload, settings.JWT_KEY, algorithm="HS256")
    return token


def get_request_user(request: request) -> User:
    """
    从request中判定当前用户
    :param request:
    :return User:
    """
    try:
        token = request.headers["token"]
        key = settings.JWT_KEY
        info = jwt.decode(token, key, algorithms=["HS256"])
        # exam expiration time
        if info["exp"] < timezone.now().timestamp():
            return AnonymousUser()
        # get user
        user = User.objects.get(id=info["id"])
        print(user.username)
        # exam username
        if user.username != info["username"]:
            return AnonymousUser()
        return user
    except:
        return AnonymousUser()


def check_request_user(request: request, id: numbers, message="无权操作！") -> User:
    """
    从request中判定当前用户
    :param request
    :param id
    :param message
    :return User:
    """
    user = get_request_user(request)
    if user.id != id and not user.is_superuser:
        raise ForbiddenException(message)
    return user
