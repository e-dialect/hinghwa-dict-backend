import demjson
from django.contrib.auth.models import User
from django.http import JsonResponse

from utils.exception.types.unauthorized import UnauthorizedException
from utils.token import get_request_user
from website.views import sendNotification


class Notifications:
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
