from django.http import JsonResponse
from django.middleware.common import MiddlewareMixin

from .types.common import CommonException

class ExceptionMiddleware(MiddlewareMixin):
    """统一异常处理中间件"""

    def process_exception(self, request, exception)->JsonResponse:
        """
        统一异常处理
        :param request: 请求对象
        :param exception: 异常对象
        :return:
        """
        if isinstance(exception, Exception):
            return CommonException(exception).response()
        return exception.response()