from django.urls import path

from .views import *

app_name = 'website'

urlpatterns = [
    path('email', email),
    # path('/<int:id>/password',),
    # path('/app',),
    # path('/forget',),
]
