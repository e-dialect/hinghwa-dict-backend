from ..models import Rewards


# 返回商品信息
def rewards_all(rewards: Rewards) -> dict:
    response = {
        "name": rewards.name,
        "point": rewards.point,
        "id": rewards.id,
        "left": rewards.left,
        "picture": rewards.picture,
        "detail": rewards.detail,
    }

    return response
