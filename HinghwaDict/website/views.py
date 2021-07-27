import random

from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


class globalVar():
    email_check = {}


def random_str(n=6):
    _str = '1234567890abcdefghijklmnopqrstuvwxyz'
    return ''.join(random.choice(_str) for i in range(n))


@csrf_exempt
@require_POST
def email(request):
    def check(email):
        return str(email).find('@') == -1

    email = request.POST['email'].replace(' ', '')
    if check(email):
        return JsonResponse(status=400)
    else:
        try:
            code = random_str()
            subject = '[兴化语记]验证码'
            msg = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
</head>
<body>
    <p><strong>亲爱的用户：</strong></p>
    <div style="margin-left: 20px"><p>你的验证码为：<strong>{0}</strong></p></div>
    <p>兴化语记团队</p>
    <p>{1}</p>
</body>
</html>'''.format(code, timezone.now().date())
            send_mail(subject, 'aaa', from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[email, ],
                      html_message=msg)
            globalVar.email_check[email] = code
            return JsonResponse({}, status=200)
        except:
            return JsonResponse({}, status=500)
