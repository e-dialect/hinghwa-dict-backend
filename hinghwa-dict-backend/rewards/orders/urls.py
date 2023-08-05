from django.urls import path

from .views.Manage_all import *
from .views.Manage_single import *

app_name = "rewards.orders"
urlpatterns = [
    path("", csrf_exempt(ManageAllOrders.as_view())),
    path("/<str:order_id>", csrf_exempt(ManageSingleOrder.as_view())),
]
