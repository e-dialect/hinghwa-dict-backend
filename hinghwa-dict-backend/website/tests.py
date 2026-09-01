import os
import tempfile
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from website.notification.utils import sendNotification
from website.storage import download_file
from website.utils import filterInOrder, random_str
from website.views import files


class WebsiteUtilityTests(SimpleTestCase):
    def test_filter_in_order_uses_requested_id_order(self):
        first = Mock(id=1)
        second = Mock(id=2)

        self.assertEqual(filterInOrder([first, second], [2, 1]), [second, first])

    def test_random_str_digit_only_contract(self):
        value = random_str(n=20, digit_only=True)

        self.assertEqual(len(value), 20)
        self.assertTrue(value.isdigit())


class NotificationUtilityTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user("sender")
        self.first_recipient = User.objects.create_user("first")
        self.second_recipient = User.objects.create_user("second")

    @patch("website.notification.utils.notify.send")
    def test_send_notification_keeps_recipient_queryset(self, notify_send):
        note = Mock(id=42)
        notify_send.return_value = [(None, [note])]
        recipients = User.objects.filter(
            id__in=[self.first_recipient.id, self.second_recipient.id]
        )

        result = sendNotification(self.sender, recipients, "测试通知")

        self.assertEqual(result, [42])
        self.assertIs(notify_send.call_args.kwargs["recipient"], recipients)

    @patch("website.notification.utils.notify.send")
    def test_send_notification_wraps_single_recipient(self, notify_send):
        note = Mock(id=43)
        notify_send.return_value = [(None, [note])]

        result = sendNotification(self.sender, self.first_recipient, "测试通知")

        self.assertEqual(result, [43])
        self.assertEqual(
            notify_send.call_args.kwargs["recipient"], [self.first_recipient]
        )


class UploadLimitTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(MAX_UPLOAD_SIZE=5)
    @patch("website.views.token_check")
    def test_direct_upload_rejects_file_before_writing(self, token_check):
        token_check.return_value = Mock(id=7)
        upload = SimpleUploadedFile("large.png", b"123456", content_type="image/png")
        request = self.factory.post("/files", {"file": upload}, HTTP_TOKEN="token")

        response = files(request)

        self.assertEqual(response.status_code, 413)

    @override_settings(MAX_UPLOAD_SIZE=5)
    @patch("website.storage.upload_file")
    @patch("website.storage.requests.get")
    def test_remote_download_rejects_large_content_length(
        self, requests_get, upload_file
    ):
        response = Mock()
        response.headers = {"Content-Length": "6"}
        requests_get.return_value = response

        with tempfile.TemporaryDirectory() as media_root, override_settings(
            MEDIA_ROOT=media_root
        ):
            result = download_file(
                "https://example.com/avatar.png", "download", "7", "avatar.png"
            )

        self.assertIsNone(result)
        requests_get.assert_called_once_with(
            "https://example.com/avatar.png", stream=True, timeout=(5, 30)
        )
        upload_file.assert_not_called()

    @override_settings(MAX_UPLOAD_SIZE=5)
    @patch("website.storage.upload_file")
    @patch("website.storage.requests.get")
    def test_remote_download_removes_partial_oversized_file(
        self, requests_get, upload_file
    ):
        response = Mock()
        response.headers = {}
        response.iter_content.return_value = [b"123", b"456"]
        requests_get.return_value = response

        with tempfile.TemporaryDirectory() as media_root, override_settings(
            MEDIA_ROOT=media_root
        ):
            result = download_file(
                "https://example.com/avatar.png", "download", "7", "avatar.png"
            )
            path = os.path.join(media_root, "download", "7", "avatar.png")
            self.assertFalse(os.path.exists(path))

        self.assertIsNone(result)
        upload_file.assert_not_called()
