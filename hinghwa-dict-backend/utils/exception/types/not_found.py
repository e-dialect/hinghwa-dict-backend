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


class CommentNotFoundException(NotFoundException):
    """
    评论不存在异常
    """

    def __init__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "评论{}不存在！".format(id)


class NotBoundWechat(NotFoundException):
    """
    微信未绑定异常
    """

    def __init__(self, username=""):
        super().__init__()
        self.status = 404
        self.msg = "账户 {}微信未绑定".format(username)


class NotBoundEmail(NotFoundException):
    """
    邮箱未绑定异常
    """

    def __init__(self, username=""):
        super().__init__()
        self.status = 404
        self.msg = "账户 {}邮箱未绑定, 请通过微信进行操作".format(username)


class ProductsNotFoundException(NotFoundException):
    """
    商品不存在
    param id:商品id
    """

    def __int__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "商品{}不存在".format(id)


class TitleNotFoundException(NotFoundException):
    """
    头衔不存在
    param id:头衔id
    """

    def __init__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "头衔{}不存在".format(id)


class TransactionsNotFoundException(NotFoundException):
    """
    积分记录不存在
    param id:积分记录id
    """

    def __init__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "积分记录{}不存在".format(id)


class OrdersNotFoundException(NotFoundException):
    """
    订单不存在
    param id:订单id
    """

    def __init__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "订单{}不存在".format(id)


class ListsNotFoundException(NotFoundException):
    """
    词单不存在
    param id:词单id
    """

    def __init__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "词单{}不存在".format(id)


class PronunciationNotFoundException(NotFoundException):
    """
    语音条不存在异常
    parma id:语音id
    """

    def __init__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "语音{}不存在！".format(id)


class PaperNotFoundException(NotFoundException):
    """
    试卷不存在异常
    parma id:试卷id
    """

    def __init__(self, id=""):
        super().__init__()
        self.status = 404
        self.msg = "试卷{}不存在！".format(id)
