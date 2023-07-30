from ...models import Products


# 返回商品信息
def products_all(products: Products) -> dict:
    response = {
        "name": products.name,
        "points": products.points,
        "id": products.id,
        "quantity": products.quantity,
        "picture": products.picture,
        "details": products.details,
    }

    return response
