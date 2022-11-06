from django.urls import path

from .views import *

app_name = "word.character"

urlpatterns = [
    path("", searchCharacters),
    path("/<int:id>", manageCharacter),
    path("/add", load_character),
    path("/words", searchEach),
    path("/words/v2", searchEachV2),
    path("/pinyin", searchCharactersPinyin),
]
