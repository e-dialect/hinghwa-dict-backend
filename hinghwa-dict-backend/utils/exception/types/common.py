from django.http import JsonResponse


class CommonException(Exception):
    """
    公共异常类
    """

    def __init__(self):
        super().__init__()
        self.status = 500
        self.msg = str(super())

    def __str__(self):
        return self.msg

    def response(self):
        return JsonResponse({"msg": self.msg}, status=self.status)
