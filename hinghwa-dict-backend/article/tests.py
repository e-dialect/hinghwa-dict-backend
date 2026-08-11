import json
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase
from django.utils import timezone

from article.models import Article, Comment
from article.views import CommentArticle, CommentDetail
from user.models import UserInfo
from utils.exception.types.unauthorized import UnauthorizedException


class CommentViewerStateTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.author = self._create_user("author")
        self.commenter = self._create_user("commenter")
        self.viewer = self._create_user("viewer")
        self.article = Article.objects.create(
            author=self.author,
            update_time=timezone.now(),
            title="测试文章",
            content="正文",
            cover="https://example.com/cover.jpg",
            visibility=True,
        )
        self.root_comment = Comment.objects.create(
            user=self.commenter,
            article=self.article,
            content="顶层评论",
        )
        self.child_comment = Comment.objects.create(
            user=self.author,
            article=self.article,
            parent=self.root_comment,
            content="作者回复",
        )
        self.root_comment.like_users.add(self.viewer)

    @staticmethod
    def _create_user(username):
        user = User.objects.create_user(username)
        UserInfo.objects.create(user=user, nickname=username)
        return user

    @patch("article.views.token_user")
    @patch("article.views.token_pass")
    def test_comment_list_includes_consistent_viewer_state(
        self, token_pass, token_user
    ):
        token_pass.return_value = "token"
        token_user.return_value = self.viewer
        request = self.factory.get(
            f"/articles/{self.article.id}/comments",
            HTTP_TOKEN="token",
        )

        response = CommentArticle().get(request, self.article.id)

        payload = json.loads(response.content)
        self.assertEqual(len(payload["comments"]), 1)
        result = payload["comments"][0]
        self.assertEqual(result["comment"]["id"], self.root_comment.id)
        self.assertEqual(
            [child["id"] for child in result["comment"]["children"]],
            [self.child_comment.id],
        )
        self.assertEqual(
            result["me"],
            {"like": True, "is_author": False, "author_replied": True},
        )

    @patch("article.views.token_pass", side_effect=UnauthorizedException())
    def test_anonymous_comment_list_has_false_personal_state(self, token_pass):
        request = self.factory.get(f"/articles/{self.article.id}/comments")

        response = CommentArticle().get(request, self.article.id)

        result = json.loads(response.content)["comments"][0]
        self.assertEqual(
            result["me"],
            {"like": False, "is_author": False, "author_replied": True},
        )

    def test_comment_detail_uses_same_viewer_state_shape(self):
        request = self.factory.get(f"/articles/comments/{self.root_comment.id}")
        request.user = AnonymousUser()

        response = CommentDetail().get(request, self.root_comment.id)

        self.assertEqual(
            json.loads(response.content)["me"],
            {"like": False, "is_author": False, "author_replied": True},
        )
