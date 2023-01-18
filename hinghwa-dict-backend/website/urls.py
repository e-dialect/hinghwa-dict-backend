from django.urls import path

from .notification.views import Notifications
from .views import *

app_name = "website"

urlpatterns = [
    path("email", email),
    path("files", files),
    path("announcements", announcements),
    path("hot_articles", hot_articles),
    path("word_of_the_day", word_of_the_day),
    path("carousel", carousel),
    path("daily-expression/<int:id>", manageDailyExpression),
    path("daily-expression", searchDailyExpression),
    path("notifications", csrf_exempt(Notifications.as_view())),
    path("notifications/<int:id>", manageNotification),
    path("notifications/unread", manageNotificationUnread),
    # path('test', test)
]
