import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from website.views import token_check
from .forms import MusicForm
from .models import Music


@csrf_exempt
def searchMusic(request):
    try:
        if request.method == 'GET':
            # TODO 正式版search
            musics = [music.id for music in Music.objects.all()]
            return JsonResponse({"music": musics}, status=200)
        elif request.method == 'POST':
            body = demjson.decode(request.body)
            token = request.headers['token']
            user = token_check(token, '***REMOVED***')
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
            body = demjson.decode(request.body)
            musics = []
            result = Music.objects.filter(id__in=body['music'])
            for music in result:
                musics.append({'music': {"id": music.id, "source": music.source, "title": music.title,
                                         "artist": music.artist, "cover": music.cover, "likes": music.likes,
                                         "contributor": music.contributor.id, "visibility": music.visibility},
                               'contributor': {'id': music.contributor.id,
                                               'nickname': music.contributor.user_info.nickname,
                                               'avatar': music.contributor.user_info.avatar}})
            return JsonResponse({"music": musics}, status=200)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def manageMusic(request, id):
    try:
        music = Music.objects.filter(id=id)
        if music.exists():
            music = music[0]
            if request.method == 'GET':
                user = music.contributor
                return JsonResponse({"music": {"id": music.id, "source": music.source, "title": music.title,
                                               "artist": music.artist, "cover": music.cover, "likes": music.likes,
                                               "contributor": {"id": user.id, 'username': user.username,
                                                               'nickname': music.contributor.user_info.nickname,
                                                               'email': user.email,
                                                               'telephone': user.user_info.telephone,
                                                               'registration_time': user.date_joined.__format__(
                                                                   '%Y-%m-%d %H:%M:%S'),
                                                               'login_time': user.last_login.__format__(
                                                                   '%Y-%m-%d %H:%M:%S') if user.last_login else '',
                                                               'birthday': user.user_info.birthday,
                                                               'avatar': user.user_info.avatar,
                                                               'county': user.user_info.county,
                                                               'town': user.user_info.town,
                                                               'is_admin': user.is_superuser},
                                               "visibility": music.visibility}}, status=200)
            elif request.method == 'PUT':
                body = demjson.decode(request.body)
                token = request.headers['token']
                user = token_check(token, '***REMOVED***', music.contributor.id)
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
                user = token_check(token, '***REMOVED***', music.contributor.id)
                if user:
                    music.delete()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)
