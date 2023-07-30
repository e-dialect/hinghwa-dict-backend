import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..dto.title_all import title_all
from utils.exception.types.not_found import TitleNotFoundException
from ...models import Title
from ..forms import TitleInfoForm
from django.views import View
from utils.exception.types.bad_request import BadRequestException
from utils.token import token_pass
import random
from utils.generate_id import generate_title_id


class ManageAllTitles(View):
    # RE0205获取全部头衔信息
    @csrf_exempt
    def get(self, request):
        min = request.GET.get("min")
        max = request.GET.get("max")
        filters = {
            "points__gte": min,
            "points__lte": max,
        }

        result_titles = Title.objects.filter(**filters)
        amount = str(result_titles.count())

        titles = []
        for title in result_titles:
            titles.append(title_all(title))

        return JsonResponse(
            {
                "result": titles,
                "amount": amount,
            },
            status=200,
        )

    # RE0201上传新头衔
    @csrf_exempt
    def post(self, request) -> JsonResponse:
        token = token_pass(request.headers, -1)
        body = demjson.decode(request.body)
        title_form = TitleInfoForm(body)
        if not title_form.is_valid():
            raise BadRequestException()
        title = title_form.save(commit=False)
        title.id = generate_title_id()
        title.save()
        return JsonResponse({"id": title.id}, status=200)
