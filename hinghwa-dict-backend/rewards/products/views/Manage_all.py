import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..dto.product_all import product_all
from ..models.product import Product
from ..forms import ProductInfoForm
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
        products_form = ProductInfoForm(body)
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

        filters = {}
        if min:
            filters["points__gte"] = min
        if max:
            filters["points__lte"] = max
        if stock == "0":
            filters["quantity"] = 0
        elif stock == "1":
            filters["quantity__gt"] = 0

        result_products = Product.objects.filter(**filters)

        amount = str(result_products.count())

        products = []
        for product in result_products:
            products.append(product_all(product))

        return JsonResponse(
            {"result": products, "amount": amount, "page": page, "pageSize": pageSize},
            status=200,
        )
