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


class ManageSingleProducts(View):
    # RE0104获取指定商品信息
    @csrf_exempt
    def get(self, request, id):
        product = Products.objects.filter(id=id)
        if not product.exists():
            raise ProductsNotFoundException()
        product = product[0]
        return JsonResponse({"products": products_all(product)}, status=200)

    # RE0102 删除商品
    @csrf_exempt
    def delete(self, request, id) -> JsonResponse:
        token = token_pass(request.headers, -1)
        products = Products.objects.filter(id=id)
        if not products.exists():
            raise ProductsNotFoundException()
        products = products[0]
        products.delete()
        return JsonResponse({}, status=200)

    # RE0103 更新商品信息
    @csrf_exempt
    def put(self, request, id) -> JsonResponse:
        token = token_pass(request.headers, -1)
        products = Products.objects.filter(id=id)
        if not products.exists():
            raise ProductsNotFoundException()
        products = products[0]
        body = demjson.decode(request.body)
        for key in body:
            setattr(products, key, body[key])
        products.save()
        return JsonResponse(products_all(products), status=200)
