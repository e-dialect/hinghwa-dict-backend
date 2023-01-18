from user.models import User
from utils.exception.types.not_found import UserNotFoundException


def get_user_by_id(id) -> User:
    try:
        return User.objects.get(id=id)
    except User.DoesNotExist:
        raise UserNotFoundException(id)
