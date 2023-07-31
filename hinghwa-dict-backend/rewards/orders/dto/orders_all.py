from ..models.order import Order
from user.dto.user_simple import user_simple


def orders_all(orders: Order):
    response = {
        "user": user_simple(orders.user),
        "address": orders.address,
        "full_name": orders.full_name,
        "telephone": orders.telephone,
        "comment": orders.comment,
        "id": orders.id,
    }

    return response
