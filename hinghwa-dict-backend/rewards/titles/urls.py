from django.urls import path

from .views.Manage_single import ManageSingleTitle
from .views.Manage_all import ManageAllTitles
from django.views.decorators.csrf import csrf_exempt

app_name = "rewards.titles"

urlpatterns = [
    path("", csrf_exempt(ManageAllTitles.as_view())),
    path("/<str:id>", csrf_exempt(ManageSingleTitle.as_view())),
]
