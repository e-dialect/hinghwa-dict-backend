import demjson
from ...models import List, Word
from ..dto.list_all import list_all
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from ...forms import ListForm
from utils.token import token_pass, token_user
from utils.generate_id import generate_list_id
from utils.exception.types.bad_request import BadRequestException
from utils.exception.types.not_found import WordNotFoundException
from django.utils import timezone


class ManageAllLists(View):
    # WD0601 创建词单
    @csrf_exempt
    def post(self, request):
        token = token_pass(request.headers, -1)
        user = token_user(token)
        body = demjson.decode(request.body)
        list_form = ListForm(body)
        if not list_form.is_valid():
            raise BadRequestException()
        for id in body["words"]:
            word = Word.objects.get(id=id)
        list = list_form.save(commit=False)
        list.createTime = timezone.now()
        list.updateTime = timezone.now()
        list.author = user
        list.id = generate_list_id()
        for id in body["words"]:
            word = Word.objects.get(id=id)
            list.save()
            list.words.add(word)
        return JsonResponse(list_all(list), status=200)

    # WD0605查找词单(多)
    def get(self, request):
        total_list = List.objects.all()
        result = []
        for list in total_list:
            result.append(list_all(list))
        return JsonResponse({"total": len(result), "lists": result})
