from django.urls import path

from .views import *

app_name = "word.application"

urlpatterns = [
    path(
        "/applications", csrf_exempt(MultiApplication.as_view())
    ),  # WD0401POST WD0403GET
    path("/applications/<int:id>", manageApplication),  # WD0402GET WD0404PUT
]
