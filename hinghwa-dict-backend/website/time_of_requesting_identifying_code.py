import time
from utils.exception.types.bad_request import IdentifyingCodeInDate

time_needed = 30
request_time = {}


class TimeOfRequestingIdentifyingCode:
    """
    用于对于存储上一次请求验证码的时间的字典进行操作的主类
    """

    def add_request_time(email, req_t):
        request_time.update({email: req_t})

    def clear_buffer(req_t):
        for i in list(request_time.keys()):
            if request_time[i] - req_t >= time_needed:
                del request_time[i]

    def accept_request(email):
        req_t = time.time()
        if (not request_time.get(email)) or (
            req_t - request_time.get(email) >= time_needed
        ):
            TimeOfRequestingIdentifyingCode.add_request_time(email, req_t)
            TimeOfRequestingIdentifyingCode.clear_buffer(req_t)
        else:
            raise IdentifyingCodeInDate()
