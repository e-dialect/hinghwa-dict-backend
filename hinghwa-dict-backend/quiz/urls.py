from django.urls import path
from .views import *
from .paper.view.paper_record_all import *
from .quiz_record.view.quiz_record_all import *
from .quiz_record.view.quiz_record_single import *
from .paper.view.paper_record_single import *

app_name = "users"

urlpatterns = [
    path("", csrf_exempt(MultiQuiz.as_view())),  # QZ0102  QZ0201
    path("/<int:id>", csrf_exempt(SingleQuiz.as_view())),  # QZ0101 QZ0103  QZ0104
    path("/<int:id>/visibility", csrf_exempt(ManageVisibility.as_view())),  # QZ0105
    path("/random", csrf_exempt(RandomQuiz.as_view())),  # QZ0202

    path("/records", csrf_exempt(QuizRecordAll.as_view())),  # QZ0401 QZ0402
    path(
        "/records/<str:record_id>", csrf_exempt(QuizRecordSingle.as_view())
    ),  # QZ0403 QZ0404
]
