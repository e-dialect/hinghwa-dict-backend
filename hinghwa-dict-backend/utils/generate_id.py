from rewards.transactions.models.transaction import Transaction
from rewards.titles.models.title import Title
from rewards.products.models.product import Product
from rewards.orders.models.order import Order
from word.models import List


def generate_transaction_id():
    last_transaction = Transaction.objects.order_by("-id").first()
    if last_transaction:
        last_id = int(last_transaction.id[2:])
        new_id = last_id + 1
    else:
        new_id = 1
    return f"JL{new_id:06d}"


def generate_title_id():
    last_title = Title.objects.order_by("-id").first()
    if last_title:
        last_id = int(last_title.id[2:])
        new_id = last_id + 1
    else:
        new_id = 1
    return f"TX{new_id:06d}"


def generate_product_id():
    last_product = Product.objects.order_by("-id").first()
    if last_product:
        last_id = int(last_product.id[2:])
        new_id = last_id + 1
    else:
        new_id = 1
    return f"SP{new_id:06d}"


def generate_order_id():
    last_order = Order.objects.order_by("-id").first()
    if last_order:
        last_id = int(last_order.id[2:])
        new_id = last_id + 1
    else:
        new_id = 1
    return f"DD{new_id:06d}"


def generate_list_id():
    last_order = List.objects.order_by("-id").first()
    if last_order:
        last_id = int(last_order.id[2:])
        new_id = last_id + 1
    else:
        new_id = 1
    return f"CD{new_id:06d}"
