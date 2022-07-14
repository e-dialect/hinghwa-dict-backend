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

from user import views as user
from website import views as website
from word import word, pronunciation, character

urlpatterns = [
    path("admin", admin.site.urls),
    # path('home/',TemplateView.as_view(template_name="home.html"),name='home')
    path("users/", include("user.urls", namespace="users")),
    path("login/", include("user.urls", namespace="login")),
    path("users", user.router_users),
    path("login", user.login),
    path("articles", include("article.urls", namespace="article")),
    path("music", include("music.urls", namespace="music")),
    path("website/", include("website.urls", namespace="website")),
    path("files/<type>/<id>/<Y>/<M>/<D>/<X>", website.openUrl),
    path(
        "words",
        include(
            [
                path("", word.searchWords), # WD0102POST    WD0201GET   WD0202PUT
                path("/<int:id>", word.manageWord), # WD0101GET WD0103PUT
                path("/add", word.load_word),   # WD0301POST
                path("/upload_standard", word.upload_standard), # WD0302POST
                path("/applications", word.searchApplication),  # WD0401POST    WD0403GET
                path("/applications/<int:id>", word.manageApplication), # WD0402GET WD0404PUT
            ]
        ),
    ),
    path(
        "characters",
        include(
            [
                path("", character.searchCharacters),
                path("/<int:id>", character.manageCharacter),
                path("/add", character.load_character),
                path("/words", character.searchEach),
                path("/words/v2", character.searchEachV2),
                path("/pinyin", character.searchCharactersPinyin),
            ]
        ),
    ),
    path(
        "pronunciation",
        include(
            [
                path("", pronunciation.searchPronunciations),
                path("/<int:id>", pronunciation.managePronunciation),
                path("/combine", pronunciation.combinePronunciationV2),
                path("/translate", pronunciation.translatePronunciation),
                path(
                    "/<int:id>/visibility", pronunciation.managePronunciationVisibility
                ),
                path("/<int:id>/examine", pronunciation.managePronunciationVisibility),
                path("/<str:ipa>", pronunciation.combinePronunciation),
            ]
        ),
    ),
    path("record", word.record),    # PN0301GET
]
