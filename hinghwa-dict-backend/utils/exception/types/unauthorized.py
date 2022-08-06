from .common import CommonException


class UnauthorizedException(CommonException):
    """
    未登录异常
    """

    def __init__(self, msg="未登录"):
        super().__init__()
        self.status = 401
        self.msg = msg


class OutdatedException(UnauthorizedException):
    """
    登录过期异常
    """

    def __init__(self):
        super().__init__("登录过期，请重新登录")


class InvalidTokenException(UnauthorizedException):
    """
    无效的token异常
    """

    def __init__(self):
        super().__init__("token无效，请重新登录")


class WrongPassword(UnauthorizedException):
    """
    (旧）密码错误
    """

    def __init__(self):
        super().__init__("（旧）密码错误")
