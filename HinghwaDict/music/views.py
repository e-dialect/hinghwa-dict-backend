import demjson
import jwt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .forms import MusicForm
from .models import Music, User


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
            user_form = jwt.decode(token, '***REMOVED***', algorithms=['HS256'])
            user = User.objects.get(id=user_form['id'])
            if user.username == user_form['username']:
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
            # 批量返回
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=400)


@csrf_exempt
def manageMusic(request, id):
    body = demjson.decode(request.body)
    try:
        music = Music.objects.get(id=id)
        if request.method == 'GET':
            return JsonResponse({"source": music.source, "title": music.title,
                                 "artist": music.artist, "cover": music.cover,
                                 "likes": music.likes, "contributor": music.contributor.username,
                                 "visibility": music.visibility}, status=200)
        elif request.method == 'PUT':
            token = request.headers['token']
            user_form = jwt.decode(token, '***REMOVED***', algorithms=['HS256'])
            user = User.objects.get(id=user_form['id'])
            if user.username == user_form['username'] and \
                    (user == music.contributor or user.is_superuser == True):
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
            user_form = jwt.decode(token, '***REMOVED***', algorithms=['HS256'])
            user = User.objects.get(id=user_form['id'])
            if user.username == user_form['username'] and \
                    (user == music.contributor or user.is_superuser == True):
                music.delete()
                return JsonResponse({}, status=200)
            else:
                return JsonResponse({}, status=401)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=400)
