from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from website.notification.utils import sendNotification
from website.utils import filterInOrder, random_str


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
