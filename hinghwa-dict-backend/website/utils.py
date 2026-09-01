# -*-coding:utf-8-*-
import math
import random

import jwt
from django.contrib.auth.models import User
from django.utils import timezone


class globalVar:
    email_code = {}


def email_check(email, code):
    email = str(email)
    if (
        (email in globalVar.email_code)
        and globalVar.email_code[email][0] == code
        and (timezone.now() - globalVar.email_code[email][1]).seconds < 600
    ):
        globalVar.email_code.pop(email)
        return 1
    else:
        return 0


def token_check(token, key, id=0):
    """
    id=-1表示要求管理员权限
    id=x表示用户id需要为x
    id=0表示任意用户都允许通过，
    成功满足要求的验证则自动刷新时长，100分钟未操作则自动超时
    :param token:
    :param key:
    :param id:
    :return:
    """
    try:
        info = jwt.decode(token, key, algorithms=["HS256"])
        if info["exp"] < timezone.now().timestamp():
            return 0
        user = User.objects.get(id=info["id"])
        if user.username == info["username"] and (
            id == 0 or id == info["id"] or user.is_superuser
        ):
            return user
        else:
            return 0
    except Exception:
        return 0


def compare(test, key):
    total = 0
    j = 0
    m = len(key)
    hint = 0
    for character in test:
        if character == key[j]:
            if j == m - 1:
                j = 0
                total += 1
                hint += 1
            else:
                j += 1
        elif j:
            total += math.pow(10, j - m)
            if j > m / 2:
                hint += 1
            j = 1 if character == key[0] else 0
    if j:
        total += math.pow(10, j - m)
        if j > m / 2:
            hint += 1
    return total + (math.pow(10, hint * math.ceil(m / 2) - len(test)) if hint else 0)


def ReLu(x: float):
    return x if x < 50 else (x - 50) * 0.01 + 50


def evaluate(standard, key, alpha=1):
    total = 0
    key = str(key).lower()
    for item, score in standard:
        item = str(item).lower().replace(" ", "")
        if len(item) > 0:
            total += (
                (compare(item, key) + compare(item[::-1], key[::-1]))
                * score
                / math.log(1 + alpha * ReLu(len(item)))
            )
    return total


def random_str(n=6, digit_only=False):
    if not digit_only:
        _str = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    else:
        _str = "1234567890"
    return "".join(random.choice(_str) for i in range(n))


def filterInOrder(objs, order) -> list:
    """
    将id为order顺序排序objs,len(objs)<=len(order)
    :param objs:待排序的数组
    :param order:
    :return:
    """
    mapping = {}
    num = 0
    for id in order:
        mapping[id] = num
        num += 1
    result = [0] * len(order)
    for item in objs:
        result[mapping[item.id]] = item
    result1 = []
    for item in result:
        if item:
            result1.append(item)
    return result1
