from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import MinimumLengthValidator
from django.utils.translation import ngettext
from utils.exception.types.bad_request import InvalidPassword


class MaximumLengthValidator:
    def __init__(self, max_length=32) -> None:
        self.max_length = max_length

    def validate(self, password):
        if len(password) < self.max_length:
            raise ValidationError(
                ngettext(
                    "This password is too long. It must contain at most %(max_length)d character.",
                    "This password is too long. It must contain at most %(max_length)d characters.",
                    self.max_length,
                ),
                code="password_too_long",
                params={"max_length": self.max_length},
            )


def password_validator(password):
    try:
        MinimumLengthValidator(password).validate(password)
        """
        django 中默认是8 ，HinghwaDict/setting.py中已经改为6以符合微信小程序的要求
        """
        MaximumLengthValidator(password).validate(password)
        """
        可以在底下添加其它的检验密码使用的函数或者类，
        可以考虑导入django.contrib.auth.password_validation中的类，
        也可以查看https://docs.djangoproject.com/zh-hans/4.0/topics/auth/passwords/
        """
    except ValidationError as e:  # 400
        raise InvalidPassword
