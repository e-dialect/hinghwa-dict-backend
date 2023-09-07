import demjson
from ...models import List, Word
from ..dto.list_all import list_all
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from ...forms import ListForm
from utils.exception.types.not_found import ListsNotFoundException
from utils.token import token_pass
from utils.generate_id import generate_list_id
from utils.exception.types.bad_request import BadRequestException


class ManageSingleLists(View):
    # WD0602删除词单
    @csrf_exempt
    def delete(self, request, list_id):
        token_pass(request.headers, -1)
        list = List.objects.filter(id=list_id)
        if not list.exists():
            raise ListsNotFoundException()
        list = list[0]
        list.delete()
        return JsonResponse({}, status=200)

    # WD0603更改词单信息
    def put(self, request, list_id):
        token_pass(request.headers, -1)
        list = List.objects.filter(id=list_id)
        if not list.exists():
            raise ListsNotFoundException()
        list = list[0]
        body = demjson.decode(request.body)
        for key in body:
            if key != "words":
                setattr(list, key, body[key])
            else:
                for id in body["words"]:
                    Word.objects.get(id=id)
                list.words.clear()
                for id in body["words"]:
                    word = Word.objects.get(id=id)
                    list.words.add(word)
        list.save()
        return JsonResponse(list_all(list), status=200)

    # WD0604查看词单(单)
    def get(self, request):
        token_pass(request.headers, 0)
        list_id = request.GET["list_id"]
        list = List.objects.filter(id=list_id)
        if not list.exists():
            raise ListsNotFoundException()
        list = list[0]
        return JsonResponse(list_all(list), status=200)
