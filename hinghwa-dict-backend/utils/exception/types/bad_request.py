from .common import CommonException


class BadRequestException(CommonException):
    """
    错误请求异常
    """

    def __init__(self, msg="请求错误"):
        super().__init__()
        self.status = 400
        self.msg = msg


class InvalidPassword(BadRequestException):
    """
    密码不符合规范异常
    """

    def __init__(self, msg="密码不符合规范异常"):
        super().__init__(msg)


class InsufficientQuiz(BadRequestException):
    """
    可用Quiz不足异常
    """

    def __init__(self, msg="可用测试题不足"):
        super().__init__(msg)


class RankWithoutDays(BadRequestException):
    """
    发音排名请求没有发送天数异常
    """

    def __init__(self, msg="排名请求没有发送天数"):
        super().__init__(msg)


class InvalidPronunciation(BadRequestException):
    """
    添加语音的请求不符合格式要求异常
    """

    def __init__(self, msg="添加的语音的请求不符合格式要求"):
        super().__init__(msg)


class ReturnUsersNumException(BadRequestException):
    """
    在点赞时请求发送的返回前多少个点赞人数这一项为空
    """

    def __init__(
        self,
        msg="请在return_users_num字段中加入请求的点赞人数，要求为正整数，或者不发送return_users_num字段",
    ):
        super().__init__(msg)
