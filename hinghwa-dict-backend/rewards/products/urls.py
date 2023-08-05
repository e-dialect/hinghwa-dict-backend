from django.urls import path

from .views.Manage_single import *
from .views.Manage_all import *

app_name = "rewards.products"

urlpatterns = [
    path("", csrf_exempt(ManageAllProducts.as_view())),
    path("/<str:id>", csrf_exempt(ManageSingleProducts.as_view())),
]
