import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from website.views import token_check
from .forms import MusicForm
from .models import Music


@csrf_exempt
def searchMusic(request):
    body = demjson.decode(request.body)
    try:
        if request.method == 'GET':
            # TODO 正式版search
            musics = [music.id for music in Music.objects.all()]
            return JsonResponse({"music": musics}, status=200)
        elif request.method == 'POST':
            token = request.headers['token']
            user = token_check(token, 'dxw')
            if user:
                music_form = MusicForm(body)
                if music_form.is_valid():
                    music = music_form.save(commit=False)
                    music.contributor = user
                    music.save()
                    return JsonResponse({"id": music.id}, status=200)
                else:
                    return JsonResponse({}, status=400)
            else:
                return JsonResponse({}, status=401)
        elif request.method == 'PUT':
            musics = []
            for id in body['music']:
                music = Music.objects.get(id=id)
                user = music.contributor
                musics.append({"id": music.id, "source": music.source, "title": music.title,
                               "artist": music.artist, "cover": music.cover, "likes": music.likes,
                               "contributor": music.contributor.id, "visibility": music.visibility})
            return JsonResponse({"music": musics}, status=200)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=400)


@csrf_exempt
def manageMusic(request, id):
    body = demjson.decode(request.body)
    try:
        music = Music.objects.get(id=id)
        if request.method == 'GET':
            user = music.contributor
            return JsonResponse({"music": {"id": music.id, "source": music.source, "title": music.title,
                                           "artist": music.artist, "cover": music.cover, "likes": music.likes,
                                           "contributor": {"id": user.id, 'username': user.username,
                                                           'nickname': info.nickname,
                                                           'email': user.email, 'telephone': user.user_info.telephone,
                                                           'registration_time': user.date_joined,
                                                           'login_time': user.last_login,
                                                           'birthday': user.user_info.birthday,
                                                           'avatar': user.user_info.avatar,
                                                           'county': user.user_info.county, 'town': user.user_info.town,
                                                           'is_admin': user.is_superuser},
                                           "visibility": music.visibility}}, status=200)
        elif request.method == 'PUT':
            token = request.headers['token']
            user = token_check(token, 'dxw', music.contributor.id)
            if user:
                body = body['music']
                music_form = MusicForm(body)
                for key in body:
                    if len(music_form[key].errors.data):
                        return JsonResponse({}, status=400)
                for key in body:
                    setattr(music, key, body[key])
                music.save()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
        elif request.method == 'DELETE':
            token = request.headers['token']
            user = token_check(token, 'dxw', music.contributor.id)
            if user:
                music.delete()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=400)
