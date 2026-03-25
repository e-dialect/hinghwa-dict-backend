from django.urls import path

from .views import *

app_name = "articles"

urlpatterns = [
    path("", csrf_exempt(SearchArticle.as_view())),
    path("/<int:id>", csrf_exempt(ManageArticle.as_view())),
    path("/<int:id>/visibility", csrf_exempt(ManageVisibility.as_view())),
    path("/<int:id>/like", csrf_exempt(LikeArticle.as_view())),
    path("/<int:id>/comments", csrf_exempt(CommentArticle.as_view())),
    path("/comments/<int:id>/like", csrf_exempt(LikeComment.as_view())),
    path("/comments/<int:id>", csrf_exempt(CommentDetail.as_view())),
    path("/comments", csrf_exempt(SearchComment.as_view())),
    path("/ranking", csrf_exempt(ArticleRanking.as_view())),  # AT0203文章榜单
]
