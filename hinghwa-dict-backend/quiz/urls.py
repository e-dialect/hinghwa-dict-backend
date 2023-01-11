from django.urls import path

from .views import *

app_name = "users"

urlpatterns = [
    path("", csrf_exempt(MultiQuiz.as_view())),  # QZ0102  QZ0201
    path("/<int:id>", csrf_exempt(SingleQuiz.as_view())),  # QZ0101 QZ0103  QZ0104
    path("/<int:id>/visibility", csrf_exempt(ManageVisibility.as_view())),  # QZ0105
    path("/random", csrf_exempt(RandomQuiz.as_view())),  # QZ0202
    path("/paper", csrf_exempt(QuizPaper.as_view())),  # QZ0203
]
