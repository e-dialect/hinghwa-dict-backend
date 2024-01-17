from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .view.cert_all import *
from .view.cert_single import *

app_name = "quiz.certs"

urlpatterns = [
    path("", csrf_exempt(AllCert.as_view())),
    path("/<str:id>", csrf_exempt(SingleCert.as_view())),
]
