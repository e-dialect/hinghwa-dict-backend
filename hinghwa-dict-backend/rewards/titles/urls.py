from django.urls import path

from .view.Manage_single import *
from .view.Manage_all import *

app_name = "rewards.titles"

urlpatterns = [
    path("", csrf_exempt(ManageAllTitles.as_view())),
    path("/<str:id>", csrf_exempt(ManageSingleTitle.as_view())),
]
