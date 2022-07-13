import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from website.views import token_check, simpleUserInfo, filterInOrder
from .forms import MusicForm
from .models import Music
from django.conf import settings
from .dto.music_all import music_all


@csrf_exempt
def searchMusic(request):
    try:
        if request.method == "GET":
            musics = Music.objects.filter(visibility=True)
            if "artist" in request.GET:
                musics = musics.filter(artist=request.GET["artist"])
            if "contributor" in request.GET:
                musics = musics.filter(contributor__username=request.GET["contributor"])
            musics = list(musics)
            musics.sort(key=lambda item: item.title)
            musics = [music.id for music in musics]
            return JsonResponse({"music": musics}, status=200)
        elif request.method == "POST":
            body = demjson.decode(request.body)
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY)
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
        elif request.method == "PUT":
            body = demjson.decode(request.body)
            result = Music.objects.filter(id__in=body["music"])
            result = filterInOrder(result, body["music"])
            musics = []
            for music in result:
                musics.append(
                    {
                        "music": {
                            "id": music.id,
                            "source": music.source,
                            "title": music.title,
                            "artist": music.artist,
                            "cover": music.cover,
                            "likes": music.like(),
                            "contributor": music.contributor.id,
                            "visibility": music.visibility,
                        },
                        "contributor": simpleUserInfo(music.contributor),
                    }
                )
            return JsonResponse({"music": musics}, status=200)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def manageMusic(request, id):
    try:
        music = Music.objects.filter(id=id)
        if music.exists():
            music = music[0]
            # MC0104 获取音乐信息
            if request.method == "GET":
                return JsonResponse({"music": music_all(music)}, status=200)
            elif request.method == "PUT":
                body = demjson.decode(request.body)
                token = request.headers["token"]
                user = token_check(token, settings.JWT_KEY, music.contributor.id)
                if user:
                    body = body["music"]
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
            elif request.method == "DELETE":
                token = request.headers["token"]
                user = token_check(token, settings.JWT_KEY, music.contributor.id)
                if user:
                    music.delete()
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


@csrf_exempt
def like(request, id):
    try:
        music = Music.objects.filter(id=id)
        if music.exists() and music[0].visibility:
            music = music[0]
            token = request.headers["token"]
            user = token_check(token, settings.JWT_KEY)
            if user:
                if request.method == "POST":
                    music.like_users.add(user)
                    return JsonResponse({}, status=200)
                elif request.method == "DELETE":
                    if len(music.like_users.filter(id=user.id)):
                        music.like_users.remove(user)
                    else:
                        return JsonResponse({}, status=400)
                    return JsonResponse({}, status=200)
                else:
                    return JsonResponse({}, status=405)
            else:
                return JsonResponse({}, status=401)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


# /music/<int:id>/visibility
@csrf_exempt
def visiblity(request, id):
    try:
        music = Music.objects.filter(id=id)
        if not music.exists():
            return JsonResponse({}, status=404)
        music = music[0]
        # MC0105 设置音乐可见性
        if request.method == "PUT":
            music.visibility = not music.visibility
            music.save()
            return JsonResponse(music_all(music), status=200)
        else:
            return JsonResponse({}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)
