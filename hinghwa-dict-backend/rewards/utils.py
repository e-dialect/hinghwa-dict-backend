from .models import Rewards, Title
from utils.exception.types.not_found import RewardsNotFoundException


def get_rewards_by_id(id) -> Rewards:
    try:
        return Rewards.objects.get(id=id)
    except Rewards.DoesNotExist:
        raise RewardsNotFoundException(id)
