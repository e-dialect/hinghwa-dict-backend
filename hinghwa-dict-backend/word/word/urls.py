from django.urls import path

from .views import *

app_name = "word.word"

urlpatterns = [
    path("", searchWords),  # WD0102POST WD0201GET WD0202PUT
    path(
        "/<int:id>", csrf_exempt(ManageWord.as_view())
    ),  # WD0101GET WD0103PUT WD0104DELETE
    path("/add", load_word),  # WD0301POST
    path("/upload_standard", upload_standard),  # WD0302POST
    path("/phonetic_ordering", csrf_exempt(PhoneticOrdering.as_view())),  # WD0501
    path("/dictionary", csrf_exempt(DictionarySearch.as_view())),  # WD0502
]
