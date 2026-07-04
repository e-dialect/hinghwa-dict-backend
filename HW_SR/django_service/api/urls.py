from __future__ import annotations

from django.urls import path

from .views import health_view, query_by_id_view, query_by_word_view, query_view


urlpatterns = [
    path("health/", health_view, name="health"),
    path("query/id/<int:word_id>/", query_by_id_view, name="query-by-id"),
    path("query/word/<str:word>/", query_by_word_view, name="query-by-word"),
    path("query/<str:query>/", query_view, name="query-with-path"),
    path("query/", query_view, name="query"),
]