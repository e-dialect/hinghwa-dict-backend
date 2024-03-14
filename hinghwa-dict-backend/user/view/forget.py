import demjson3
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views import View

from utils.PasswordValidation import password_validator
from utils.exception.types.forbidden import ForbiddenException
from utils.exception.types.not_found import NotBoundEmail
from utils.token import check_request_user
from website.views import email_check


class Forget(View):
    # LG0201 返回用户邮箱
    def get(self, request):
        user = User.objects.filter(username=request.GET["username"])
        if user.exists():
            user = user[0]
            email = user.email
            if email:
                return JsonResponse({"email": email}, status=200)
            else:
                raise NotBoundEmail(user.user_info.nickname)
        else:
            return JsonResponse({}, status=404)

    # LG0202 重置密码
    def put(self, request, id):
        # 检查验证码并重置用户密码
        body = demjson3.decode(request.body)
        user = check_request_user(request, id)
        if user.username != body["username"]:
            raise ForbiddenException("用户名不匹配")
        if user.email != body["email"]:
            raise ForbiddenException("邮箱不匹配")
        if email_check(body["email"], body["code"]):
            password_validator(body["password"])
            user.set_password(body["password"])
            user.save()
            return JsonResponse({}, status=200)
        else:
            return JsonResponse({"msg": "验证码错误"}, status=400)
