import demjson
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..dto.orders_all import orders_all
from utils.exception.types.not_found import OrdersNotFoundException
from django.conf import settings
from ..models.order import Order
from ..forms import OrdersInfoForm
from django.views import View
from utils.exception.types.bad_request import BadRequestException
from utils.token import token_pass
from user.utils import get_user_by_id
from django.utils import timezone


class ManageSingleOrder(View):
    # RE0404获取指定订单信息
    @csrf_exempt
    def get(self, request, order_id):
        order = Order.objects.filter(id=order_id)
        if not order.exists():
            raise OrdersNotFoundException()
        order = order[0]
        user_id = order.user.id
        token = token_pass(request.headers, -1) or token_pass(request.headers, user_id)
        if token:
            return JsonResponse(orders_all(order), status=200)
        else:
            return JsonResponse({"msg": "无权限"}, status=403)

    # RE0402删除订单
    @csrf_exempt
    def delete(self, request, order_id):
        order = Order.objects.filter(id=order_id)
        if not order.exists():
            raise OrdersNotFoundException()
        order = order[0]
        user_id = order.user.id
        token = token_pass(request.headers, -1) or token_pass(request.headers, user_id)
        if token:
            order.delete()
            return JsonResponse({}, status=200)
        else:
            return JsonResponse({"msg": "无权限"}, status=403)

    # RE0403更新订单信息
    @csrf_exempt
    def put(self, request, order_id):
        order = Order.objects.filter(id=order_id)
        if not order.exists():
            raise OrdersNotFoundException()
        order = order[0]
        user_id = order.user.id
        token = token_pass(request.headers, -1) or token_pass(request.headers, user_id)
        if token:
            body = demjson.decode(request.body)

            for key in body:
                setattr(order, key, body[key])
                order.timestamp = timezone.now()
            order.save()
            return JsonResponse(orders_all(order), status=200)
        else:
            return JsonResponse({}, status=403)
