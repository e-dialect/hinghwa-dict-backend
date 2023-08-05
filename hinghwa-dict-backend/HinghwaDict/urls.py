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
from word.word import views as word

urlpatterns = [
    path("admin/", admin.site.urls),
    # path('home/',TemplateView.as_view(template_name="home.html"),name='home')
    #   以下使用命名空间划分url
    path("users/", include("user.urls", namespace="users")),
    path("login/", include("user.urls", namespace="login")),
    path("users", user.router_users),
    path("login", user.login),
    path("articles", include("article.urls", namespace="article")),
    path("music", include("music.urls", namespace="music")),
    path("website/", include("website.urls", namespace="website")),
    path("quizzes", include("quiz.urls", namespace="quiz")),
    path("files/<type>/<id>/<Y>/<M>/<D>/<X>", website.openUrl),
    path("words", include("word.word.urls", namespace="word.word")),
    path(
        "words",
        include("word.application.urls", namespace="word.application"),
    ),
    path(
        "characters",
        include("word.character.urls", namespace="word.character"),
    ),
    path(
        "pronunciation",
        include("word.pronunciation.urls", namespace="word.pronunciation"),
    ),
    path("record", word.record),  # PN0301GET
    path("products", include("rewards.products.urls", namespace="rewards.products")),
    path("titles", include("rewards.titles.urls", namespace="rewards.titles")),
    path(
        "transactions",
        include("rewards.transactions.urls", namespace="rewards.transactions"),
    ),
    path("orders", include("rewards.orders.urls", namespace="rewards.orders")),
]
