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
    """
    检验（新）密码是否符合规范
    """
    if len(password) < 6 or len(password) > 32:
        raise InvalidPassword
