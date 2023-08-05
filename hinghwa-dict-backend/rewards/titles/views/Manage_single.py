import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..dto.title_all import title_all
from utils.exception.types.not_found import TitleNotFoundException
from ..models.title import Title
from django.views import View
from utils.token import token_pass


class ManageSingleTitle(View):
    # RE0204获取单个头衔信息
    @csrf_exempt
    def get(self, request, id):
        title = Title.objects.filter(id=id)
        if not title.exists():
            raise TitleNotFoundException()
        title = title[0]
        return JsonResponse({"titles": title_all(title)}, status=200)

    # RE0202删除头衔
    @csrf_exempt
    def delete(self, request, id) -> JsonResponse:
        token_pass(request.headers, -1)
        title = Title.objects.filter(id=id)
        if not title.exists():
            raise TitleNotFoundException()
        title = title[0]
        title.delete()
        return JsonResponse({}, status=200)

    # RE0203更新头衔信息
    @csrf_exempt
    def put(self, request, id) -> JsonResponse:
        token_pass(request.headers, -1)
        title = Title.objects.filter(id=id)
        if not title.exists():
            raise TitleNotFoundException()
        title = title[0]
        body = demjson.decode(request.body)
        for key in body:
            setattr(title, key, body[key])
        title.save()
        return JsonResponse({"titles": title_all(title)}, status=200)
