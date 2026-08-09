from .models import Notesheet, Notification

def unread_notesheets(request):
    if request.user.is_authenticated:
        notesheets_count = Notesheet.objects.filter(
            current_holder=request.user,
            is_seen=False
        ).count()
        return {
            'unread_notesheets_count': notesheets_count,
        }
    return {
        'unread_notesheets_count': 0,
    }

def notifications_processor(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False)[:5]
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {
            'unread_notifications': unread_notifications,
            'unread_notifications_count': unread_count
        }
    return {}
