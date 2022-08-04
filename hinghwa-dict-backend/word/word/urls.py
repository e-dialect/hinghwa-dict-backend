from django.urls import path

from .views import *

app_name = "word.word"

urlpatterns = [
    path("", searchWords),  # WD0102POST WD0201GET WD0202PUT
    path("/<int:id>", manageWord),  # WD0101GET WD0103PUT
    path("/add", load_word),  # WD0301POST
    path("/upload_standard", upload_standard),  # WD0302POST
]