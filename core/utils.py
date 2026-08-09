from django.urls import reverse
from .models import Notification

def create_notification(recipient, sender, title, message, link='', notification_type='notesheet'):
    """
    Helper function to create a notification for a user.
    """
    if recipient != sender:
        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            title=title,
            message=message,
            link=link,
            notification_type=notification_type
        )
