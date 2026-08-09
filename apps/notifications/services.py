from notifications.models import Notification


def create_notification(user, title, body):
    """
    ایجاد یک نوتیفیکیشن جدید برای کاربر.

    Args:
        user: نمونهٔ User که نوتیفیکیشن برای او ساخته می‌شود.
        title: عنوان نوتیفیکیشن.
        body: متن اصلی نوتیفیکیشن.

    Returns:
        Notification instance.
    """
    return Notification.objects.create(user=user, title=title, body=body)