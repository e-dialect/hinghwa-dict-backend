from .common import CommonException


class BadRequestExcption(CommonException):
    """
    错误请求异常
    """

    def __init__(self, msg="请求错误"):
        super().__init__()
        self.status = 400
        self.msg = msg
