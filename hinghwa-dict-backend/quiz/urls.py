from django.urls import path
from .paper.view.manage_all import *
from .paper.view.manage_single import *
from .views import *

app_name = "users"

urlpatterns = [
    path("", csrf_exempt(MultiQuiz.as_view())),  # QZ0102  QZ0201
    path("/<int:id>", csrf_exempt(SingleQuiz.as_view())),  # QZ0101 QZ0103  QZ0104
    path("/<int:id>/visibility", csrf_exempt(ManageVisibility.as_view())),  # QZ0105
    path("/random", csrf_exempt(RandomQuiz.as_view())),  # QZ0202
    path("/paper", csrf_exempt(ManageAllPaper.as_view())),  # QZ0203
    path("/paper/<str:paper_id>", csrf_exempt(ManageSinglePaper.as_view())),
]
