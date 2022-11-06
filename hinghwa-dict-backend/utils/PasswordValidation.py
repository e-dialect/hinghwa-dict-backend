from utils.exception.types.bad_request import InvalidPassword


def password_validator(password):
    """
    检验（新）密码是否符合规范
    """
    if len(password) < 6 or len(password) > 32:
        raise InvalidPassword
