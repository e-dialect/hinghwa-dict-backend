from .common import CommonException


class ForbiddenException(CommonException):
    """
    权限不足异常
    """

    def __init__(self, msg="您无权进行此操作"):
        super().__init__()
        self.status = 403
        self.msg = msg


class OnlyAdminException(ForbiddenException):
    """
    只有管理员才能操作异常
    """

    def __init__(self):
        super().__init__("仅限管理员！")
