from django.urls import path

from .views import *

app_name = "users"

urlpatterns = [
    path("", csrf_exempt(SearchMusic.as_view())),  # MC0101    MC0201  MC0202
    path("/<int:id>", csrf_exempt(ManageMusic.as_view())),  # MC0102    MC0103  MC0104
    path("/<int:id>/like", csrf_exempt(LikeMusic.as_view())),  # MC0301    MC0302
    path("/<int:id>/visibility", csrf_exempt(VisibilityMusic.as_view())),  # Mc0105
]
