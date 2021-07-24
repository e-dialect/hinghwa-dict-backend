import demjson
import jwt
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from website.views import globalVar, random_str
from .forms import UserForm, UserInfoForm
from .models import UserInfo, User


@require_POST
@csrf_exempt
def register(request):
    try:
        user_form = UserForm(request.POST)
        code = request.POST['code']
        if user_form.is_valid():
            if user_form.cleaned_data['email'] in globalVar.email_check:
                if globalVar.email_check[user_form.cleaned_data['email']] == code:
                    user = user_form.save(commit=False)
                    user.set_password(user_form.cleaned_data['password'])
                    user.save()
                    user_info = UserInfo.objects.create(user=user, nickname='用户{}'.format(random_str()))
                    globalVar.email_check.pop(user_form.cleaned_data['email'])
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
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            user.last_login = timezone.now()
            user.save()
            payload = {'username': username, 'id': user.id,
                       'login_time': timezone.now().__format__('%Y-%m-%d %H:%M:%S')}
            return JsonResponse({"token": jwt.encode(payload, 'dxw', algorithm='HS256')},
                                status=200)
        else:
            return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=400)


@csrf_exempt
def manageInfo(request, id):
    try:
        token = request.headers['token']
        user_form = jwt.decode(token, 'dxw', algorithms=['HS256'])
        user = User.objects.get(id=user_form['id'])
        if user.username == user_form['username']:
            if request.method == 'GET':
                info = user.user_info
                return JsonResponse({'username': user.username, 'nickname': info.nickname,
                                     'email': user.email, 'telephone': info.telephone,
                                     'registration_time': user.date_joined, 'login_time': user.last_login,
                                     'birthday': info.birthday, 'avatar': info.avatar,
                                     'county': info.county, 'town': info.town,
                                     'is_admin': user.is_superuser}, status=200)
            elif request.method == 'PUT':
                info = demjson.decode(request.body)['user']
                user_form = UserForm(info)
                user_info_form = UserInfoForm(info)
                if ~(("email" in info) and len(user_form['email'].errors.data)) and \
                        ~(("username" in info) and len(user_form['username'].errors.data) and info[
                            'username'] != user.username) \
                        and user_info_form.is_valid():
                    if 'username' in info:
                        user.username = info['username']
                    if 'email' in info:
                        user.email = info['email']
                    if 'nickname' in info:
                        user.user_info.nickname = info['nickname']
                    if 'telephone' in info:
                        user.user_info.telephone = info['telephone']
                    if 'birthday' in info:
                        user.user_info.birthday = info['birthday']
                    if 'avatar' in info:
                        user.user_info.avatar = info['avatar']
                    if 'county' in info:
                        user.user_info.county = info['county']
                    if 'town' in info:
                        user.user_info.town = info['town']
                    user.save()
                    user.user_info.save()

                    payload = {'username': user.username, 'id': user.id,
                               'login_time': timezone.now().__format__('%Y-%m-%d %H:%M:%S')}
                    return JsonResponse({"token": jwt.encode(payload, 'dxw', algorithm='HS256')},
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
        user_form = jwt.decode(token, 'dxw', algorithms=['HS256'])
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
    token = request.headers['token']
    try:
        user_form = jwt.decode(token, 'dxw', algorithms=['HS256'])
        user = User.objects.get(id=user_form['id'])
        body = demjson.decode(request.body)
        if user.username == body['username']:
            if request.method == 'GET':
                return JsonResponse({"email": user.email}, status=200)
            elif request.method == 'PUT':
                email = body['email']
                if email in globalVar.email_check and globalVar.email_check[email] == body['code']:
                    user.set_password(body['password'])
                    globalVar.email_check.pop(email)
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=400)
