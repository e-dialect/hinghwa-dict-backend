from rewards.models import Transactions, Title, Products, Orders


def generate_transaction_id():
    last_transaction = Transactions.objects.order_by("-id").first()
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
    last_product = Products.objects.order_by("-id").first()
    if last_product:
        last_id = int(last_product.id[2:])
        new_id = last_id + 1
    else:
        new_id = 1
    return f"SP{new_id:06d}"


def generate_order_id():
    last_order = Orders.objects.order_by("-id").first()
    if last_order:
        last_id = int(last_order.id[2:])
        new_id = last_id + 1
    else:
        new_id = 1
    return f"DD{new_id:06d}"
