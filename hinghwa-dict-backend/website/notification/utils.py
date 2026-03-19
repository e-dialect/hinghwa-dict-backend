# -*-coding:utf-8-*-
from django.contrib.auth.models import User
from django.db.models import Q
from notifications.models import Notification
from notifications.signals import notify


def sendNotification(
    sender, recipients, content, target=None, action_object=None, title=None
):
    """
    发送站内通知，recipients为列表，若为None表示向管理员发送通知
    """
    if recipients is None:
        transfer = User.objects.get(id=2)
        result = sendNotification(
            sender, [transfer], content, target, action_object, title
        )
        recipients = User.objects.filter(is_superuser=True)
        target = Notification.objects.get(id=result[0])
        sendNotification(transfer, recipients, content, target, action_object, title)
        return result
    if sender is None:
        sender = User.objects.get(id=2)
    if title is None:
        title = f"【通知】{sender.username} 回复了你"
    if not isinstance(recipients, (list, tuple)):
        recipients = [recipients]
    result = notify.send(
        sender,
        recipient=recipients,
        verb=title,
        description=content,
        target=target,
        action_object=action_object,
    )
    return [note.id for note in result[0][1]]


def readNotification(notification):
    if isinstance(notification.target, Notification):
        notification.target.unread = False
        notification.target.save()
        Notification.objects.filter(
            Q(target_content_type=notification.target_content_type)
            & Q(target_object_id=notification.target_object_id)
        ).mark_all_as_read()
    else:
        notification.unread = False
        notification.save()
