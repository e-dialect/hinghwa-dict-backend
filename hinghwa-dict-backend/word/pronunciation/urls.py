from django.urls import path

from .views import *
from .views import SearchPronunciations, ManageApproval, PronunciationRanking

app_name = "word.pronunciation"

urlpatterns = [
    path("", csrf_exempt(SearchPronunciations.as_view())),
    path("/<int:id>", managePronunciation),
    path("/combine", combinePronunciationV2),
    path("/translate", translatePronunciation),
    path("/<int:id>/visibility", csrf_exempt(ManageApproval.as_view())),
    path("/<int:id>/examine", csrf_exempt(ManageApproval.as_view())),
    path("/ranking", csrf_exempt(PronunciationRanking.as_view())),  # PN0205语音榜单
    path("/<str:ipa>", combinePronunciation),
]
