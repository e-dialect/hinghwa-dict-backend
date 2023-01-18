import demjson
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views import View
from notifications.models import Notification

from utils.exception.types.bad_request import BadRequestException
from utils.exception.types.unauthorized import UnauthorizedException
from utils.token import get_request_user
from website.notification.dto import notification_normal
from website.views import sendNotification
from django.core.paginator import Paginator


class Notifications(View):
    # WS0801 send notification
    def post(self, request):
        user = get_request_user(request)
        if not user.id:
            raise UnauthorizedException()
        body = demjson.decode(request.body)
        if len(body["recipients"]) == 1 and body["recipients"][0] == -1:
            recipients = None
        else:
            recipients = User.objects.filter(id__in=body["recipients"])
        title = body["title"] if "title" in body else None
        notifications = sendNotification(user, recipients, body["content"], title=title)
        return JsonResponse({"notifications": notifications}, status=200)

    # WS0802 filter notifications
    def get(self, request):
        notifications = Notification.objects.all()
        if "from" in request.GET:
            notifications = notifications.filter(actor_object_id=request.GET["from"])
        if "to" in request.GET:
            notifications = notifications.filter(recipient_id=request.GET["to"])
        if "unread" in request.GET:
            if request.GET["unread"] in ["True", "true", "1"]:
                notifications = notifications.filter(unread=True)
            elif request.GET["unread"] in ["False", "false", "0"]:
                notifications = notifications.filter(unread=False)
            else:
                raise BadRequestException("unread should be True or False")

        page_size = int(request.GET.get("pageSize", 10))
        page = int(request.GET.get("page", 1))
        pages = Paginator(notifications, page_size)
        return JsonResponse(
            {
                "notifications": [
                    notification_normal(notification)
                    for notification in pages.page(page)
                ],
                "total": notifications.count(),
                "pages": pages.num_pages,
            },
            status=200,
        )
