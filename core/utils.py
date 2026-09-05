from django.urls import reverse
from .models import Notification

def create_notification(recipient, sender, title, message, link='', notification_type='notesheet', allow_self=False):
    """
    Helper function to create a notification for a user.
    Set allow_self=True to send a confirmation notification to the sender themselves.
    """
    if allow_self or recipient != sender:
        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            title=title,
            message=message,
            link=link,
            notification_type=notification_type
        )
