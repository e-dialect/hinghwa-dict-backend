from django.urls import path

from .views import *

app_name = 'articles'

urlpatterns = [
    path('', searchArticle),
    path('/<int:id>', manageArticle),
    path('/<int:id>/visibility', manageArticleVisibility),
    path('/<int:id>/like', like),
    path('/<int:id>/comments', comment),
    path('/comments', searchComment)
]
