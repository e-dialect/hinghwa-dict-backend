import time
from utils.exception.types.bad_request import IdentifyingCodeInDate

time_needed = 30


class VerificationCodeCache:
    """
    用于对于存储上一次请求验证码的时间的字典进行操作的主类
    """

    def __new__(cls, *args, **kwargs):  # 这里不能使用__init__，因为__init__是在instance已经生成以后才去调用的
        if cls.__instance is None:
            cls.__instance = super(VerificationCodeCache, cls).__new__(
                cls, *args, **kwargs
            )
        return cls.__instance

    request_time = {}

    def add_request_time(self, key, req_t):
        self.request_time.update({key: req_t})

    def clear_buffer(self, req_t):
        for i in list(self.request_time.keys()):
            if self.request_time[i] - req_t >= time_needed:
                del self.request_time[i]

    def accept_request(self, email, scene):
        req_t = time.time()
        key = email + scene
        if (not self.request_time.get(key)) or (
            req_t - self.request_time.get(key) >= time_needed
        ):
            VerificationCodeCache.add_request_time(self, key, req_t)
            VerificationCodeCache.clear_buffer(req_t)
        else:
            raise IdentifyingCodeInDate()
