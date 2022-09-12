import time
from utils.exception.types.bad_request import IdentifyingCodeInDate

time_needed = 30
request_time = {}


class TimeOfRequestingIdentifyingCode:
    def add_request_time(id, req_t):
        request_time.update({id: req_t})

    def clear_buffer(req_t):
        for i in list(request_time.keys()):
            if request_time[i] - req_t >= time_needed:
                del request_time[i]

    def check_available(id):
        req_t = time.time()
        if (not request_time.get(id)) or (req_t - request_time.get(id) >= time_needed):
            TimeOfRequestingIdentifyingCode.add_request_time(id, req_t)
            TimeOfRequestingIdentifyingCode.clear_buffer(req_t)
        else:
            raise IdentifyingCodeInDate()
