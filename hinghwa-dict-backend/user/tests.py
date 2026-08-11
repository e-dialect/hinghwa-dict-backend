from unittest.mock import patch

from django.test import SimpleTestCase

from utils.Upload import TRUSTED_AVATAR_HOSTS, uploadAvatar
from utils.exception.types.not_found import NotFoundException


class UploadAvatarDeduplicationTests(SimpleTestCase):
    @patch("utils.Upload.download_file")
    def test_trusted_avatar_urls_are_not_downloaded_again(self, download_file):
        for host in TRUSTED_AVATAR_HOSTS:
            avatar = f"https://{host}/avatars/existing.png"
            with self.subTest(host=host):
                self.assertEqual(uploadAvatar(7, avatar), avatar)

        download_file.assert_not_called()

    @patch("utils.Upload.download_file")
    def test_external_avatar_is_downloaded_once(self, download_file):
        download_file.return_value = "https://cos.edialect.top/files/avatar.png"

        result = uploadAvatar(7, "https://example.com/avatar.png")

        self.assertEqual(result, download_file.return_value)
        download_file.assert_called_once()

    @patch("utils.Upload.download_file", return_value=None)
    def test_failed_external_avatar_download_has_explicit_error(self, download_file):
        with self.assertRaisesMessage(NotFoundException, "头像上传失败"):
            uploadAvatar(7, "https://example.com/missing.png")

        download_file.assert_called_once()
