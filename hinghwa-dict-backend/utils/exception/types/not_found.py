from .common import CommonException


class NotFoundException(CommonException):
    """
    资源不存在异常
    """

    def __init__(self, msg="资源不存在！"):
        super().__init__()
        self.status = 404
        self.msg = msg


class WordNotFoundException(NotFoundException):
    """
    词条不存在异常
    :param id: 词条id
    """

    def __init__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "词条{}不存在！".format(id)
