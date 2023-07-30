from django.urls import path

from .view.Search_from_id import *
from .view.Search_from_user import *

app_name = "rewards.transactions"

urlpatterns = [
    path("/<str:transaction_id>", csrf_exempt(SearchFromID.as_view())),
    path("", csrf_exempt(SearchFromUser.as_view()))
]