from django.urls import path

from .view.manage_all_list import *
from .view.manage_word_in_list import *
from .view.manage_single_list import *

app_name = "word.lists"

urlpatterns = [
    path("", csrf_exempt(ManageAllLists.as_view())),
    path("/<str:list_id>", csrf_exempt(ManageSingleLists.as_view())),
    path("/<str:list_id>/words", csrf_exempt(ManageListWords.as_view()))
]