import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..dto.orders_all import orders_all
from utils.exception.types.not_found import (
    OrdersNotFoundException,
    ProductsNotFoundException,
)
from django.conf import settings
from ...models import Orders, Products
from ..forms import OrdersInfoForm
from django.views import View
from utils.exception.types.bad_request import BadRequestException
from utils.token import token_pass, token_user
from user.utils import get_user_by_id
from utils.generate_id import generate_order_id
from utils.Rewards_action import create_transaction


class ManageAllOrders(View):
    # RE0401上传新订单
    @csrf_exempt
    def post(self, request) -> JsonResponse:
        products_id = str(request.GET.get("products_id"))
        token = token_pass(request.headers)
        user = token_user(token)
        product = Products.objects.filter(id=products_id)
        if not product.exists():
            raise ProductsNotFoundException()
        product = product[0]
        body = demjson.decode(request.body)
        if user.user_info.points_now >= product.points:
            if product.quantity > 0:
                orders_form = OrdersInfoForm(body)
                if not orders_form.is_valid():
                    raise BadRequestException()
                orders = orders_form.save(commit=False)
                orders.user = user
                orders.id = generate_order_id()
                orders.save()
                product.quantity -= 1
                product.save()
                user.user_info.points_now -= product.points
                user.user_info.save()
                action = "redeem"
                points = product.points
                user_id = user.id
                create_transaction(
                    action=action, points=points, reason="兑换商品", user_id=user_id
                )
                return JsonResponse({"id": orders.id}, status=200)
            else:
                return JsonResponse({"msg": "商品暂无库存"}, status=300)
        else:
            return JsonResponse({"msg": "用户积分不足"}, status=500)

    # RE0405获取指定用户全部订单
    @csrf_exempt
    def get(self, request):
        user_id = request.GET["user_id"]
        page = request.GET.get("page", 1)
        pageSize = request.GET.get("pageSize", 10)
        amount = 0
        results = []
        orders = Orders.objects.filter(user=get_user_by_id(user_id))
        for order in orders:
            results.append(orders_all(order))
            amount += 1
        return JsonResponse(
            {
                "result": results,
                "amount": str(amount),
                "page": str(page),
                "pageSize": str(pageSize),
            }
        )
