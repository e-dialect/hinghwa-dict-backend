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


class QuizNotFoundException(NotFoundException):
    """
    测试题不存在异常
    :param id: 测试题id
    """

    def __init__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "测试题{}不存在！".format(id)


class UserNotFoundException(NotFoundException):
    """
    用户不存在异常
    :param id: 用户id
    """

    def __init__(self, id=0):
        super().__init__()
        self.msg = "用户{}不存在！".format(id)


class MusicNotFoundException(NotFoundException):
    """
    音乐不存在异常
    ：param id:音乐id
    """

    def __init__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "音乐{}不存在！".format(id)


class ArticleNotFoundException(NotFoundException):
    """
    文章不存在异常
    ： parma id:音乐id
    """

    def __init__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "文章{}不存在！".format(id)


class ApplicationNotFoundException(NotFoundException):
    """
    词条变更申请不存在异常
    :param id: 词条变更申请id
    """

    def __init__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "词条变更申请{}不存在！".format(id)


class NotBoundWechat(NotFoundException):
    """
    微信未绑定异常
    """

    def __init__(self, msg="微信未绑定"):
        super().__init__(msg)