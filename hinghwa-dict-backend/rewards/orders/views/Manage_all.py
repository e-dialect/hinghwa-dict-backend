import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ...products.models.product import Product
from ..dto.orders_all import order_all
from utils.exception.types.not_found import (
    ProductsNotFoundException,
)
from ..forms import OrderInfoForm
from django.views import View
from utils.exception.types.bad_request import BadRequestException
from utils.token import token_pass, token_user
from user.utils import get_user_by_id
from utils.generate_id import generate_order_id
from utils.Rewards_action import create_transaction
from ..models.order import Order
from django.core.paginator import Paginator


class ManageAllOrders(View):
    # RE0401上传新订单
    @csrf_exempt
    def post(self, request) -> JsonResponse:
        products_id = str(request.GET.get("products_id"))
        token = token_pass(request.headers)
        user = token_user(token)
        product = Product.objects.filter(id=products_id)
        if not product.exists():
            raise ProductsNotFoundException()
        product = product[0]
        body = demjson.decode(request.body)
        if user.user_info.points_now < product.points:
            return JsonResponse({"msg": "用户积分不足"}, status=403)
        if product.quantity <= 0:
            return JsonResponse({"msg": "商品暂无库存"}, status=403)
        orders_form = OrderInfoForm(body)
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
        create_transaction(
            action="redeem", points=product.points, reason="兑换商品", user_id=user.id
        )
        return JsonResponse(order_all(orders), status=200)

    # RE0405获取指定用户全部订单
    @csrf_exempt
    def get(self, request):
        user_id = request.GET["user_id"]
        page = request.GET.get("page", 1)
        pageSize = request.GET.get("pageSize", 10)
        if not page:
            page = 1
        if not pageSize:
            pageSize = 10
        amount = 0
        results = []
        orders = Order.objects.filter(user=get_user_by_id(user_id))
        for order in orders:
            results.append(order_all(order))
            amount += 1
        paginator = Paginator(orders, pageSize)
        current_page = paginator.get_page(page)

        return JsonResponse(
            {
                "result": results,
                "amount": str(amount),
                "total_pages": str(paginator.num_pages),
                "page": str(current_page.number),
                "pageSize": str(pageSize),
            }
        )
