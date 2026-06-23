from django.db import models
from users.models import User


class Notification(models.Model):
    """
    مدل ذخیره‌سازی اعلان‌های درون‌برنامه‌ای.

    هر اعلان متعلق به یک کاربر است و می‌تواند خوانده‌شده یا خوانده‌نشده باشد.

    Attributes:
        user (User): کاربر دریافت‌کنندهٔ اعلان.
        title (str): عنوان کوتاه اعلان.
        body (str): متن اصلی اعلان.
        is_read (bool): آیا کاربر اعلان را خوانده است؟
        created_at (datetime): زمان ایجاد اعلان.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'اعلان'
        verbose_name_plural = 'اعلان‌ها'

    def __str__(self):
        return f"{self.title} - {self.user.phone_number}"