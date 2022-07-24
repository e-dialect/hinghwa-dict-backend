from django.urls import path

from .views import *

app_name = "word.application"

urlpatterns = [
    path("/applications", searchApplication),  # WD0401POST WD0403GET
    path("/applications/<int:id>", manageApplication),  # WD0402GET WD0404PUT
]
