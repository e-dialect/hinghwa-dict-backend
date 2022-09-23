import time
from urllib import request
from utils.exception.types.bad_request import IdentifyingCodeInDate

time_needed = 30
request_time_test = {}
request_time_US0101 = {}
request_time_LG0202 = {}


class TimeOfRequestingIdentifyingCode:
    """
    用于对于存储上一次请求验证码的时间的字典进行操作的主类
    """

    def __init__(self, email):
        self.email = email
        self.request_time = request_time_test

    def add_request_time(self, req_t):
        self.request_time.update({self.email: req_t})

    def clear_buffer(self, req_t):
        for i in list(self.request_time.keys()):
            if self.request_time[i] - req_t >= time_needed:
                del self.request_time[i]

    def accept_request(self):
        req_t = time.time()
        if (not self.request_time.get(self.email)) or (
            req_t - self.request_time.get(self.email) >= time_needed
        ):
            TimeOfRequestingIdentifyingCode.add_request_time(self.email, req_t)
            TimeOfRequestingIdentifyingCode.clear_buffer(req_t)
        else:
            raise IdentifyingCodeInDate()


class TimeOfRequestingIdentifyingCodeUS0101(TimeOfRequestingIdentifyingCode):
    """
    用于功能US0101用户注册
    """

    def __init__(self, email):
        super().__init__(email)
        self.request_time = request_time_US0101


class TimeOfRequestingIdentifyingCodeLG0202(TimeOfRequestingIdentifyingCode):
    """
    用于功能LG0202修改密码
    """

    def __init__(self, email):
        super().__init__(email)
        self.request_time = request_time_LG0202
