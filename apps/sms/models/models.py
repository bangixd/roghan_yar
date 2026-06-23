from django.db import models
from django.conf import settings

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
    code = models.CharField(max_length=50, unique=True)    # مثلاً 'birthday', 'survey', 'reminder'
    content = models.TextField(help_text="از {{variable}} استفاده کن")
    provider = models.ForeignKey(SMSProvider, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

class SMSLog(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در صف'),
        ('sent', 'ارسال شد'),
        ('failed', 'ناموفق'),
        ('delivered', 'تحویل داده شد'),
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