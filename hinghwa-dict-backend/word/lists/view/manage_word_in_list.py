import demjson
from ...models import List, Word
from ..dto.list_all import list_all
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from utils.exception.types.not_found import (
    ListsNotFoundException,
    WordNotFoundException,
)
from utils.token import token_pass
from django.utils import timezone


class ManageListWords(View):
    # WD0606增加词单词语
    @csrf_exempt
    def post(self, request):
        token_pass(request.headers, -1)
        list_id = request.GET["list_id"]
        list = List.objects.filter(id=list_id)
        if not list.exists():
            raise ListsNotFoundException()
        body = demjson.decode(request)
        for id in body["words"]:
            word = Word.objects.get(id=id)
            if not word:
                raise WordNotFoundException()
            list.words.add(word)
        list.updateTime = timezone.now()
        list.save()
        return JsonResponse(list_all(list), status=200)

    # WD0607删除词单词语
    @csrf_exempt
    def delete(self, request):
        token_pass(request.headers, -1)
        list_id = request.GET["list_id"]
        body = demjson.decode(request)
        list = List.objects.filter(id=list_id)
        if not list.exists():
            raise ListsNotFoundException()
        list = list[0]
        for id in body["words"]:
            word = Word.objects.get(id=id)
            if not word:
                raise WordNotFoundException()
            list.words.remove(word)
        list.updateTime = timezone.now()
        list.save()
        return JsonResponse({}, status=200)
