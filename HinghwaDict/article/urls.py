from django.urls import path

from .views import *

app_name = 'articles'

urlpatterns = [
    path('<int:id>', manageArticle),
    path('<int:id>/like', like),
    path('<int:id>/comment', comment),
]
