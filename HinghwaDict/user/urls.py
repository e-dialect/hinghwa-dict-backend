from django.urls import path

from .views import *

app_name = 'users'

urlpatterns = [
    path('<int:id>', manageInfo),
    path('<int:id>/pronunciation', pronunciation),
    path('<int:id>/password', updatePassword),
    path('<int:id>/email', updateEmail),
    path('app', app),
    path('forget', forget),
]
