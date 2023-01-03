from website.views import download_file, random_str
from django.utils import timezone
from utils.exception.types.common import CommonException
from utils.exception.types.not_found import NotFoundException


def uploadAvatar(id, body, suffix="png"):
    try:
        time = timezone.now().__format__("%Y_%m_%d")
        filename = time + "_" + random_str(15) + "." + suffix
        url = download_file(body["avatar"], "download", str(id), filename)
        if url is None:
            raise NotFoundException()
        return url
    except CommonException as e:  # 500
        raise e
