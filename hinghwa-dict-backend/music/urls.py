from django.urls import path

from .views import *

app_name = 'users'

urlpatterns = [
    path('', searchMusic),  #MC0101 MC0201 MC0202
    path('/<int:id>', manageMusic), #MC0102 MC0103 MC0104
    path('/<int:id>/like', like),   #MC0301 MC0302
]
