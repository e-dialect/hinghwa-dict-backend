import demjson
import jwt
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from website.views import globalVar, random_str, email_check, token_check
from .forms import UserForm, UserInfoForm
from .models import UserInfo, User


@require_POST
@csrf_exempt
def register(request):
    try:
        body = demjson.decode(request.body)
        user_form = UserForm(body)
        code = body['code']
        if user_form.is_valid():
            if email_check(user_form.cleaned_data['email'], code):
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data['password'])
                user.save()
                user_info = UserInfo.objects.create(user=user, nickname='用户{}'.format(random_str()))
                return JsonResponse({"id": user.id}, status=200)
            else:
                return JsonResponse({}, status=401)
        else:
            if user_form['username'].errors:
                return JsonResponse({}, status=409)
            else:
                return JsonResponse({}, status=400)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=500)


@csrf_exempt
@require_POST
def login(request):
    try:
        body = demjson.decode(request.body)
        username = body['username']
        password = body['password']
        user = authenticate(username=username, password=password)
        if user:
            user.last_login = timezone.now()
            user.save()
            payload = {'username': username, 'id': user.id,
                       'login_time': timezone.now().__format__('%Y-%m-%d %H:%M:%S'),
                       "value": random_str()}
            return JsonResponse({"token": jwt.encode(payload, 'dxw', algorithm='HS256')},
                                status=200)
        else:
            return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=400)


@csrf_exempt
def manageInfo(request, id):
    try:
        body = demjson.decode(request.body)
        user = User.objects.get(id=id)
        if request.method == 'GET':
            # 获取用户信息
            info = user.user_info
            return JsonResponse({"id": user.id, 'username': user.username, 'nickname': info.nickname,
                                 'email': user.email, 'telephone': info.telephone,
                                 'registration_time': user.date_joined, 'login_time': user.last_login,
                                 'birthday': info.birthday, 'avatar': info.avatar,
                                 'county': info.county, 'town': info.town,
                                 'is_admin': user.is_superuser}, status=200)
        elif request.method == 'PUT':
            # 更新用户信息
            token = request.headers['token']
            if token_check(token, 'dxw', id):
                info = body['user']
                user_form = UserForm(info)
                user_info_form = UserInfoForm(info)
                if ~(("username" in info) and len(user_form['username'].errors.data) and info['username'] != user.username) \
                        and user_info_form.is_valid():
                    if 'username' in info:
                        user.username = info['username']
                    for key in info:
                        if key != "username" and key != "email" and key != "code":
                            setattr(user.user_info, key, info[key])
                    user.save()
                    user.user_info.save()
                    payload = {'username': user.username, 'id': user.id,
                               'login_time': timezone.now().__format__('%Y-%m-%d %H:%M:%S'),
                               "value": random_str()}
                    return JsonResponse({"token": jwt.encode(payload, 'dxw', algorithm='HS256')},
                                        status=200)
                else:
                    if ~user_form.is_valid() and ('username' in info) and info['username'] != user.username:
                        return JsonResponse({}, status=409)
                    else:
                        return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=400)


@csrf_exempt
def updatePassword(request, id):
    try:
        if request.method == 'PUT':
            token = request.headers['token']
            user = User.objects.get(id=id)
            body = demjson.decode(request.body)
            if token_check(token, 'dxw', id):
                if user.check_password(body['oldpassword']):
                    user.set_password(body['newpassword'])
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def updateEmail(request,id):
    try:
        if request.method == 'PUT':
            body = demjson.decode(request.body)
            token = request.headers['token']
            user = User.objects.get(id=id)
            if token_check(token,'dxw',id) and email_check(body['email'],body['code']):
                user.email = body['email']
                user.save()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def app(request):
    pass


@csrf_exempt
def forget(request):
    try:
        body = demjson.decode(request.body)
        user = User.objects.get(username=body['username'])
        if request.method == 'GET':
            # 返回用户邮箱
            return JsonResponse({"email": user.email}, status=200)
        elif request.method == 'PUT':
            # 检查验证码并重置用户密码
            email = body['email']
            if email_check(email,body['code']):
                user.set_password(body['password'])
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=405)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=400)
