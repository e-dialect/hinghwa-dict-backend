import demjson3
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..dto.product_all import product_all
from utils.exception.types.not_found import ProductsNotFoundException
from ..models.product import Product
from django.views import View
from utils.token import token_pass


class ManageSingleProducts(View):
    # RE0104获取指定商品信息
    @csrf_exempt
    def get(self, request, id):
        product = Product.objects.filter(id=id)
        if not product.exists():
            raise ProductsNotFoundException()
        product = product[0]
        return JsonResponse({"products": product_all(product)}, status=200)

    # RE0102 删除商品
    @csrf_exempt
    def delete(self, request, id) -> JsonResponse:
        token_pass(request.headers, -1)
        products = Product.objects.filter(id=id)
        if not products.exists():
            raise ProductsNotFoundException()
        products = products[0]
        products.delete()
        return JsonResponse({}, status=200)

    # RE0103 更新商品信息
    @csrf_exempt
    def put(self, request, id) -> JsonResponse:
        token_pass(request.headers, -1)
        products = Product.objects.filter(id=id)
        if not products.exists():
            raise ProductsNotFoundException()
        products = products[0]
        body = demjson3.decode(request.body)
        for key in body:
            setattr(products, key, body[key])
        products.save()
        return JsonResponse(product_all(products), status=200)
