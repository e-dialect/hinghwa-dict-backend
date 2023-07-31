from django.urls import path

from .views.Search_from_id import *
from .views.Search_from_user import *
from django.views.decorators.csrf import csrf_exempt

app_name = "rewards.transactions"

urlpatterns = [
    path("/<str:transaction_id>", csrf_exempt(SearchFromID.as_view())),
    path("", csrf_exempt(SearchFromUser.as_view())),
]
