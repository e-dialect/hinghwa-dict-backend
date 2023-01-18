from django.core.paginator import EmptyPage
from django.http import JsonResponse
from django.middleware.common import MiddlewareMixin

from .types.common import CommonException
from .types.bad_request import BadRequestException


class ExceptionMiddleware(MiddlewareMixin):
    """统一异常处理中间件"""

    def process_exception(self, request, exception) -> JsonResponse:
        """
        统一异常处理
        :param request: 请求对象
        :param exception: 异常对象
        :return:
        """
        if isinstance(exception, EmptyPage):
            return BadRequestException(str(exception)).response()
        if isinstance(exception, KeyError):
            return BadRequestException("缺少必要参数").response()
        if isinstance(exception, ValueError):
            return BadRequestException("参数值异常").response()
        if isinstance(exception, CommonException):
            return exception.response()
        print(repr(exception))
        return CommonException(exception).response()
