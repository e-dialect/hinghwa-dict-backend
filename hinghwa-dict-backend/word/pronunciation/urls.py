from django.urls import path

from .views import *

app_name = "word.pronunciation"

urlpatterns = [
    path("", searchPronunciations),
    path("/<int:id>", managePronunciation),
    path("/combine", combinePronunciationV2),
    path("/translate", translatePronunciation),
    path("/<int:id>/visibility", managePronunciationVisibility),
    path("/<int:id>/examine", managePronunciationVisibility),
    path("/<str:ipa>", combinePronunciation),
    path("/ranking", csrf_exempt(PronunciationRanking).as_view()),  # PN0205语音审核
]
