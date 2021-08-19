"""HinghwaDict URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from article import views as article
from music import views as music
from user import views as user
from website import views as website
from word import views as word

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('home/',TemplateView.as_view(template_name="home.html"),name='home')
    path('users/', include('user.urls', namespace='users')),
    path('login/', include('user.urls', namespace='login')),
    path('users', user.register),
    path('login', user.login),
    path('articles/', include('article.urls', namespace='article')),
    path('articles', article.searchArticle),
    path('music/', include('music.urls', namespace='music')),
    path('music', music.searchMusic),
    path('website/', include('website.urls', namespace='website')),
    path('files/<type>/<id>/<Y>/<M>/<D>/<X>', website.openUrl),

    path('words', include([path('', word.searchWords),
                           path('/<int:id>', word.manageWord),
                           path('/add', word.load_word)])),
    path('characters', include([path('', word.searchCharacters),
                                path('/<int:id>', word.manageCharacter),
                                path('/add', word.load_character)])),
    path('pronunciation', include([path('', word.searchPronunciations),
                                   path('/<int:id>', word.managePronunciation)])),
]
