from django.urls import path

from .views import *

app_name = "users"

urlpatterns = [
    path("", csrf_exempt(MultiQuiz.as_view())),  # QZ0102  QZ0201
    path("/<int:id>", csrf_exempt(SingleQuiz.as_view())),  # QZ0101 QZ0103  QZ0104
    path("/random", csrf_exempt(RandomQuiz.as_view())),  # QZ0202
]
