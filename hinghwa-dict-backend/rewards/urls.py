from django.urls import path

from .views import *

app_name = "rewards"

urlpatterns = [
    path("/entity", csrf_exempt(ManageRewards.as_view())),
    path("/entity/<int:id>", csrf_exempt(SearchRewards.as_view())),
    path("/entity/<int:id>/manage", csrf_exempt(ManageRewards.as_view())),
    path("/list", csrf_exempt(SearchRewards.as_view())),
    path("/title", csrf_exempt(ManageTitle.as_view())),
    path("/title/<int:id>", csrf_exempt(SearchTitle.as_view())),
    path("/title/<int:id>/manage", csrf_exempt(ManageTitle.as_view())),
]
