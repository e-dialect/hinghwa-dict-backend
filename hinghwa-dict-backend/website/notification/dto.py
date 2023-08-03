from notifications.models import Notification

from user.dto.user_simple import user_simple


def notification_normal(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "from": user_simple(notification.actor),
        "to": user_simple(notification.recipient),
        "time": notification.timestamp.__format__("%Y-%m-%d %H:%M:%S"),
        "title": notification.verb,
        "unread": notification.unread,
        "content": notification.description,
        "public": notification.public,
    }
