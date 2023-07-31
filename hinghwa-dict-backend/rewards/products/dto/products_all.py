from ..models.product import Product


# 返回商品信息
def products_all(products: Product) -> dict:
    response = {
        "name": products.name,
        "points": products.points,
        "id": products.id,
        "quantity": products.quantity,
        "picture": products.picture,
        "details": products.details,
    }

    return response
