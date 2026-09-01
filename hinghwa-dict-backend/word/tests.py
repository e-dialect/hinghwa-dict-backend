import json
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import caches
from django.http import HttpResponseRedirect
from django.test import RequestFactory, TestCase

from user.models import UserInfo
from word.admin import ApplicationAdmin
from word.application.dto.application_all import application_all
from word.application.dto.application_simple import application_simple
from word.application.views import SingleApplication
from word.models import Application, Pronunciation, Word
from word.pronunciation.views import PronunciationRanking


class ApplicationApprovalResultTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.contributor = User.objects.create_user("contributor")
        self.reviewer = User.objects.create_superuser(
            "reviewer", email="reviewer@example.com", password="password"
        )
        UserInfo.objects.create(user=self.contributor)
        UserInfo.objects.create(user=self.reviewer)
        self.application = Application.objects.create(
            contributor=self.contributor,
            content_word="测试",
        )
        self.admin = ApplicationAdmin(Application, AdminSite())

    def _admin_request(self, action):
        request = self.factory.post("/admin/word/application/1/change/", {action: "1"})
        request.user = self.reviewer
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    @patch("word.admin.sendNotification")
    def test_admin_reject_records_explicit_failure(self, send_notification):
        request = self._admin_request("_reject")

        with patch.object(
            self.admin,
            "_get_next_application_redirect",
            return_value=HttpResponseRedirect("/admin/word/application/"),
        ):
            self.admin.response_change(request, self.application)

        self.application.refresh_from_db()
        self.assertIs(self.application.approved, False)
        self.assertEqual(self.application.verifier, self.reviewer)
        send_notification.assert_called_once()

    @patch("word.admin.sendNotification")
    def test_admin_approve_records_explicit_success(self, send_notification):
        request = self._admin_request("_approve")

        with patch.object(
            self.admin,
            "_get_next_application_redirect",
            return_value=HttpResponseRedirect("/admin/word/application/"),
        ):
            self.admin.response_change(request, self.application)

        self.application.refresh_from_db()
        self.assertIs(self.application.approved, True)
        self.assertEqual(self.application.verifier, self.reviewer)
        send_notification.assert_called_once()

    def test_legacy_review_is_not_reported_as_pending(self):
        self.application.verifier = self.reviewer
        self.application.save()

        self.assertEqual(
            self.admin.get_approval_status(self.application),
            "已审核（历史结果未知）",
        )

    @patch("word.application.views.sendNotification")
    @patch("word.application.views.token_user")
    @patch("word.application.views.token_pass")
    def test_api_reject_records_explicit_failure(
        self, token_pass, token_user, send_notification
    ):
        token_pass.return_value = "token"
        token_user.return_value = self.reviewer
        request = self.factory.put(
            f"/words/applications/{self.application.id}",
            data=json.dumps({"result": False, "reason": "内容不符合规范"}),
            content_type="application/json",
            HTTP_TOKEN="token",
        )

        response = SingleApplication().put(request, self.application.id)

        self.application.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertIs(self.application.approved, False)
        self.assertEqual(self.application.verifier, self.reviewer)
        send_notification.assert_called_once()

    def test_application_dtos_expose_approval_result(self):
        self.application.approved = False
        self.application.verifier = self.reviewer
        self.application.save()

        self.assertIs(application_all(self.application)["approved"], False)
        self.assertIs(application_simple(self.application)["approved"], False)


class PronunciationRankingNumericTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.first = self._create_user("first")
        self.second = self._create_user("second")
        self.word = Word.objects.create(
            word="测试",
            definition="测试词",
            contributor=self.first,
        )
        self._create_pronunciation(self.first)
        self._create_pronunciation(self.first)
        self._create_pronunciation(self.second)
        self._create_pronunciation(self.second, visibility=False)
        caches["pronunciation_ranking"].clear()

    @staticmethod
    def _create_user(username):
        user = User.objects.create_user(username)
        UserInfo.objects.create(user=user, nickname=username)
        return user

    def _create_pronunciation(self, contributor, visibility=True):
        return Pronunciation.objects.create(
            word=self.word,
            source="https://example.com/pronunciation.mp3",
            ipa="test",
            pinyin="test",
            county="",
            town="",
            contributor=contributor,
            visibility=visibility,
        )

    def test_ranking_returns_numeric_amounts_rank_and_pagination(self):
        request = self.factory.get(
            "/pronunciation/ranking",
            {"days": "7", "page": "1", "pageSize": "10"},
        )
        with patch("word.pronunciation.views.token_pass", return_value="token"), patch(
            "word.pronunciation.views.token_user", return_value=self.first
        ):
            response = PronunciationRanking().get(request)

        payload = json.loads(response.content)
        self.assertEqual([item["amount"] for item in payload["ranking"]], [2, 1])
        self.assertEqual(payload["me"], {"amount": 2, "rank": 1})
        self.assertEqual(payload["pagination"]["page_size"], 10)
        self.assertTrue(
            all(isinstance(item["amount"], int) for item in payload["ranking"])
        )
        self.assertIsInstance(payload["me"]["amount"], int)
        self.assertIsInstance(payload["me"]["rank"], int)

    def test_anonymous_ranking_returns_numeric_zeroes(self):
        request = self.factory.get(
            "/pronunciation/ranking",
            {"days": "7", "page": "1", "pageSize": "10"},
        )
        with patch(
            "word.pronunciation.views.token_pass", side_effect=KeyError("token")
        ):
            response = PronunciationRanking().get(request)

        self.assertEqual(json.loads(response.content)["me"], {"amount": 0, "rank": 0})
