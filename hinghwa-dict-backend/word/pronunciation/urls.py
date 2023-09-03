from django.urls import path

from .views import *
from .views import (
    SearchPronunciations,
    ManageApproval,
    PronunciationRanking,
    ManagePronunciation,
)

app_name = "word.pronunciation"

urlpatterns = [
    path("", csrf_exempt(SearchPronunciations.as_view())),
    path("/<int:id>", csrf_exempt(ManagePronunciation.as_view())),
    path("/combine", combinePronunciationV2),
    path("/translate", translatePronunciation),
    path("/<int:id>/visibility", csrf_exempt(ManageApproval.put)),  # PUT PN0105 修改审核结果
    path("/<int:id>/examine", csrf_exempt(ManageApproval.post)),  # POST PN0106 审核
    path("/ranking", csrf_exempt(PronunciationRanking.as_view())),  # PN0205语音榜单
    path("/<str:ipa>", combinePronunciation),
]
