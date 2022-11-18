import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from website.views import token_check, simpleUserInfo, filterInOrder
from .forms import MusicForm
from .models import Music
from django.conf import settings
from .dto.music_all import music_all
from .dto.music_normal import music_normal
from utils.exception.types.bad_request import BadRequestException
from utils.exception.types.common import CommonException
from utils.exception.types.not_found import MusicNotFoundException
from utils.exception.types.forbidden import ForbiddenException
from utils.token import token_pass, token_user


class SearchMusic(View):
    # MC0201 搜索符合条件的音乐
    def get(self, request) -> JsonResponse:
        musics = Music.objects.filter(visibility=True)
        if "artist" in request.GET:
            musics = musics.filter(artist=request.GET["artist"])
        if "contributor" in request.GET:
            musics = musics.filter(contributor__username=request.GET["contributor"])
        musics = list(musics)
        musics.sort(key=lambda item: item.title)
        musics = [music.id for music in musics]
        return JsonResponse({"music": musics}, status=200)

    # MC0101 上传新音乐
    def post(self, request) -> JsonResponse:
        token = token_pass(request.headers)
        user = token_user(token)
        body = demjson.decode(request.body)
        music_form = MusicForm(body)
        if not music_form.is_valid():
            raise BadRequestException()
        music = music_form.save(commit=False)
        music.contributor = user
        music.save()
        return JsonResponse({"id": music.id}, status=200)

    # MC0202 音乐批量获取
    def put(self, request) -> JsonResponse:
        body = demjson.decode(request.body)
        result = Music.objects.filter(id__in=body["music"])
        result = filterInOrder(result, body["music"])
        musics = []
        for music in result:
            musics.append(
                {
                    "music": music_normal(music),
                    "contributor": simpleUserInfo(music.contributor),
                }
            )
        return JsonResponse({"music": musics}, status=200)


class ManageMusic(View):
    # MC0104 获取音乐信息
    def get(self, request, id) -> JsonResponse:
        music = Music.objects.filter(id=id)
        if not music.exists():
            raise MusicNotFoundException()
        music = music[0]
        return JsonResponse({"music": music_all(music)}, status=200)

    # MC0103 更新音乐信息
    def put(self, request, id) -> JsonResponse:
        music = Music.objects.filter(id=id)
        if not music.exists():
            raise MusicNotFoundException()
        music = music[0]
        token = token_pass(request.headers, music.contributor.id)
        body = demjson.decode(request.body)
        body = body["music"]
        music_form = MusicForm(body)
        for key in body:
            if len(music_form[key].errors.data):
                raise BadRequestException()
        for key in body:
            setattr(music, key, body[key])
        music.save()
        return JsonResponse({}, status=200)

    # MC0102 删除音乐
    def delete(self, request, id) -> JsonResponse:
        music = Music.objects.filter(id=id)
        if not music.exists():
            raise MusicNotFoundException()
        music = music[0]
        token = token_pass(request.headers, music.contributor.id)
        music.delete()
        return JsonResponse({}, status=200)


class LikeMusic(View):
    # MC0301 给这音乐点赞
    def post(self, request, id) -> JsonResponse:
        token = token_pass(request.headers)
        user = token_user(token)
        music = Music.objects.filter(id=id)
        if not music.exists() or not music[0].visibility:
            raise MusicNotFoundException()
        music = music[0]
        music.like_users.add(user)
        return JsonResponse({}, status=200)

    # MC0302 取消这音乐点赞
    def delete(self, request, id) -> JsonResponse:
        token = token_pass(request.headers)
        user = token_user(token)
        music = Music.objects.filter(id=id)
        if not music.exists() or not music[0].visibility:
            raise MusicNotFoundException()
        music = music[0]
        if not len(music.like_users.filter(id=user.id)):
            raise BadRequestException()
        music.like_users.remove(user)
        return JsonResponse({}, status=200)


class VisibilityMusic(View):
    # MC0105 设置音乐可见性
    def put(self, request, id) -> JsonResponse:
        token = token_pass(request.headers, -1)
        music = Music.objects.filter(id=id)
        if not music.exists():
            raise MusicNotFoundException()
        music = music[0]
        music.visibility = not music.visibility
        music.save()
        return JsonResponse(music_all(music), status=200)
