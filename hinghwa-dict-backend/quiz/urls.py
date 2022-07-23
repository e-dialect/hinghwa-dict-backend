from django.urls import path

from .views import *

app_name = "quizzes"

urlpatterns = [
    path("", manageQuiz),  # QZ0102  QZ0201
    path("/<int:id>", searchQuiz),  # QZ0101 QZ0103  QZ0104
    path("/random", randomQuzi),  # MC0202
]
