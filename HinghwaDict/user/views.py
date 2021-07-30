import demjson
import jwt
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from website.views import globalVar, random_str, email_check
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
                globalVar.email_code.pop(user_form.cleaned_data['email'])
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
            return JsonResponse({"token": jwt.encode(payload, '***REMOVED***', algorithm='HS256')},
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
            user_form = jwt.decode(token, '***REMOVED***', algorithms=['HS256'])
            if id == user_form['id'] and user.username == user_form['username']:
                info = body['user']
                user_form = UserForm(info)
                user_info_form = UserInfoForm(info)
                if (("email" not in info) or (("code" in info) and email_check(info['email'], info['code']))) and \
                        ~(("username" in info) and len(user_form['username'].errors.data) and info['username'] != user.username) \
                        and user_info_form.is_valid():
                    if 'username' in info:
                        user.username = info['username']
                    if 'email' in info:
                        user.email = info['email']
                    # if 'nickname' in info:
                    #     user.user_info.nickname = info['nickname']
                    # if 'telephone' in info:
                    #     user.user_info.telephone = info['telephone']
                    # if 'birthday' in info:
                    #     user.user_info.birthday = info['birthday']
                    # if 'avatar' in info:
                    #     user.user_info.avatar = info['avatar']
                    # if 'county' in info:
                    #     user.user_info.county = info['county']
                    # if 'town' in info:
                    #     user.user_info.town = info['town']
                    for key in info:
                        if key != "username" and key != "email" and key != "code":
                            setattr(user.user_info, key, info[key])
                    user.save()
                    user.user_info.save()
                    payload = {'username': user.username, 'id': user.id,
                               'login_time': timezone.now().__format__('%Y-%m-%d %H:%M:%S'),
                               "value": random_str()}
                    return JsonResponse({"token": jwt.encode(payload, '***REMOVED***', algorithm='HS256')},
                                        status=200)
                else:
                    if ~user_form.is_valid() and ('username' in info) and info['username'] != user.username:
                        return JsonResponse({}, status=409)
                    else:
                        return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=400)


@csrf_exempt
def updatePassword(request, id):
    if request.method == 'PUT':
        token = request.headers['token']
        user_form = jwt.decode(token, '***REMOVED***', algorithms=['HS256'])
        user = User.objects.get(id=user_form['id'])
        body = demjson.decode(request.body)
        if user and user.username == user_form['username'] and id == user_form['id']:
            if user.check_password(body['oldpassword']):
                user.set_password(body['newpassword'])
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
    else:
        return JsonResponse({}, status=400)


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
            if email in globalVar.email_code and globalVar.email_code[email] == body['code']:
                user.set_password(body['password'])
                globalVar.email_code.pop(email)
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=400)
