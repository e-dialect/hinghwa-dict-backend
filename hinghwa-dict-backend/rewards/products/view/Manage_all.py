import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..dto.products_all import products_all
from utils.exception.types.not_found import ProductsNotFoundException
from django.conf import settings
from ...models import Products
from ..forms import ProductsInfoForm
from django.views import View
from utils.exception.types.bad_request import BadRequestException
from utils.token import token_pass
from utils.generate_id import generate_product_id


class ManageAllProducts(View):
    # RE0101 上传新商品
    @csrf_exempt
    def post(self, request) -> JsonResponse:
        token = token_pass(request.headers, -1)
        body = demjson.decode(request.body)
        products_form = ProductsInfoForm(body)
        if not products_form.is_valid():
            raise BadRequestException()
        products = products_form.save(commit=False)
        products.id = generate_product_id()
        products.save()
        return JsonResponse({"id": products.id}, status=200)

    # RE0105获取全部商品信息
    @csrf_exempt
    def get(self, request):
        min = request.GET.get("min")
        max = request.GET.get("max")
        pageSize = str(request.GET.get("pageSize", 10))
        page = str(request.GET.get("page", 1))
        stock = request.GET.get("stock")

        filters = {
            "points__gte": min,
            "points__lte": max,
        }

        if stock == "0":
            filters["quantity"] = 0
        elif stock == "1":
            filters["quantity__gt"] = 0

        result_products = Products.objects.filter(**filters)

        amount = str(result_products.count())

        products = []
        for product in result_products:
            products.append(products_all(product))

        return JsonResponse(
            {"result": products, "amount": amount, "page": page, "pageSize": pageSize},
            status=200,
        )
