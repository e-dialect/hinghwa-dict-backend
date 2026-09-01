from website.storage import download_file
from website.utils import random_str
from django.utils import timezone
from utils.exception.types.not_found import NotFoundException
from urllib.parse import urlparse


TRUSTED_AVATAR_HOSTS = frozenset(
    {
        "api.pxm.edialect.top",
        "cos.edialect.top",
        "cos.test.edialect.top",
        "dummyimage.com",
    }
)


def uploadAvatar(id, avatar, suffix="png"):
    if urlparse(avatar).hostname in TRUSTED_AVATAR_HOSTS:
        return avatar
    time = timezone.now().__format__("%Y_%m_%d")
    filename = time + "_" + random_str(15) + "." + suffix
    url = download_file(avatar, "download", str(id), filename)
    if url is None:
        raise NotFoundException("头像上传失败")
    return url
