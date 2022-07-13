from django.urls import path

from .views import *

app_name = 'users'

urlpatterns = [
    path('', searchMusic),
    path('/<int:id>', manageMusic),
    path('/<int:id>/like', like),
    path('/<int:id>/visibility', visiblity),
]
