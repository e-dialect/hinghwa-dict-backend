from website.views import download_file, random_str
from django.utils import timezone
from utils.exception.types.not_found import NotFoundException
from urllib.parse import urlparse


def uploadAvatar(id, avatar, suffix="png"):
    # TODO 除了默认图片外，其他照片的重复性判断
    if avatar == "https://cos.edialect.top/website/默认头像.jpg":
        return avatar
    # get domain name of avatar url
    if urlparse(avatar).netloc in [
        "api.pxm.edialect.top",
        "cos.edialect.top",
        "cos.test.edialect.top",
        "dummyimage.com",
    ]:
        return avatar
    time = timezone.now().__format__("%Y_%m_%d")
    filename = time + "_" + random_str(15) + "." + suffix
    url = download_file(avatar, "download", str(id), filename)
    if url is None:
        raise NotFoundException("头像上传失败")
    return url
