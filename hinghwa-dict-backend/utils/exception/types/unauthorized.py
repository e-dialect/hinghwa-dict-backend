from .common import CommonException


class UnauthorizedExcption(CommonException):
    """
    未登录异常
    """

    def __init__(self, msg="未登录"):
        super().__init__()
        self.status = 401
        self.msg = msg


class OutdatedException(UnauthorizedExcption):
    """
    登录过期异常
    """

    def __init__(self):
        super().__init__("登录过期，请重新登录")


class InvalidTokenException(UnauthorizedExcption):
    """
    无效的token异常
    """

    def __init__(self):
        super().__init__("token无效，请重新登录")
