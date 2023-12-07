from django.urls import path
from .view.paper_record_all import *
from .view.paper_record_single import *
from .view.manage_all import *
from .view.manage_single import *

app_name = "quiz.papers"

urlpatterns = [
    path("", csrf_exempt(ManageAllPaper.as_view())),  # QZ0203
    path("/records", csrf_exempt(PaperRecordAll.as_view())),
    path("/records/<str:record_id>", csrf_exempt(PaperRecordSingle.as_view())),
    path("/<str:paper_id>", csrf_exempt(ManageSinglePaper.as_view())),
]
