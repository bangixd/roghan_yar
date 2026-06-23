from django.db import models
from users.models import User


class SMSProvider(models.Model):
    name = models.CharField(max_length=100)
    api_key_encrypted = models.TextField()                 # در عمل رمزنگاری کن (با Fernet)
    sender_number = models.CharField(max_length=20)
    config = models.JSONField(default=dict, blank=True)    # تنظیمات اضافی
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SMSTemplate(models.Model):
    """
    قالب‌های پیامکی (پیش‌فرض سیستمی یا سفارشی هر کاربر).

    اگر فیلد user خالی باشد، قالب سیستمی است و برای همه قابل استفاده.
    در غیر این صورت فقط برای کاربر مشخص در دسترس است.

    Attributes:
        code: کد یکتای قالب (مثلاً 'welcome', 'reminder', 'birthday', 'survey').
        content: متن قالب با placeholders مثل {{name}}.
        user: کاربری که قالب را سفارشی کرده (اختیاری).
        provider: ارائه‌دهندهٔ پیش‌فرض (در صورت نیاز، می‌تواند خالی باشد).
        created_at: زمان ایجاد.
    """
    code = models.CharField(max_length=50)
    content = models.TextField(help_text="از {{variable}} استفاده کنید")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sms_templates')
    provider = models.ForeignKey('SMSProvider', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('code', 'user')  # هر کاربر برای هر کد فقط یک قالب سفارشی می‌تواند داشته باشد

    def __str__(self):
        owner = f"user {self.user_id}" if self.user else "system"
        return f"{self.code} ({owner})"

class SMSLog(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در صف'),
        ('sent', 'ارسال شد'),
        ('failed', 'ناموفق'),
        ('delivered', 'تحویل داده شد'),
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sms_logs'
    )
    provider = models.ForeignKey(SMSProvider, on_delete=models.SET_NULL, null=True)
    template = models.ForeignKey(SMSTemplate, on_delete=models.SET_NULL, null=True)
    receiver_phone = models.CharField(max_length=15)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    response_data = models.JSONField(default=dict, blank=True)
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"SMS to {self.receiver_phone} - {self.status}"


class UserSMSConfig(models.Model):
    """
    تنظیمات اختصاصی هر کاربر برای سرویس پیامک.

    هر تعویض‌روغنی می‌تواند ارائه‌دهندهٔ پیامکی خود را تنظیم کند و
    انواع مختلف پیامک‌ها را فعال/غیرفعال کند.

    Attributes:
        user: کاربر مرتبط (رابطهٔ OneToOne).
        provider_name: نام ارائه‌دهنده (مثلاً kavenegar, melipayamak).
        api_key: کلید API کاربر در سامانهٔ پیامکی.
        sender_number: شمارهٔ فرستنده.
        welcome_enabled: فعال بودن پیامک خوش‌آمدگویی.
        reminder_enabled: فعال بودن یادآوری سرویس بعدی.
        birthday_enabled: فعال بودن تبریک تولد.
        survey_enabled: فعال بودن نظرسنجی بعد از سرویس.
        is_active: فعال بودن کلی سرویس پیامک برای این کاربر.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sms_config')
    provider_name = models.CharField(max_length=50, default='kavenegar')
    api_key = models.TextField(blank=True, null=True)  # در عمل رمزنگاری شود
    sender_number = models.CharField(max_length=20, blank=True, null=True)

    # فعال‌ساز انواع پیامک‌ها
    welcome_enabled = models.BooleanField(default=True)
    reminder_enabled = models.BooleanField(default=True)
    birthday_enabled = models.BooleanField(default=True)
    survey_enabled = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SMS config for {self.user.phone_number}"