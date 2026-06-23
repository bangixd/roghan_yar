import requests
from sms.models import SMSProvider, SMSTemplate, SMSLog


class BaseSMSBackend:
    def send(self, phone, message):
        raise NotImplementedError


# مثال برای کاوه‌نگار
class KavenegarBackend(BaseSMSBackend):
    def __init__(self, api_key, sender):
        self.api_key = api_key
        self.sender = sender

    def send(self, phone, message):
        # اینجا کد واقعی ارسال رو بذار
        print(f"Simulating sending to {phone}: {message}")
        return {'status': 'sent'}


def get_active_provider():
    provider = SMSProvider.objects.filter(is_active=True).first()
    if not provider:
        raise Exception("No active SMS provider")
    # امنیتی: رمزگشایی api_key (اینجا ساده‌انگاری شده)
    if provider.name == 'Kavenegar':
        return KavenegarBackend(api_key=provider.api_key_encrypted, sender=provider.sender_number)
    # اضافه کردن ارائه‌دهنده‌های دیگر...
    raise Exception("Unsupported provider")


def send_sms(phone, template_code, context=None, provider=None):
    if context is None:
        context = {}
    try:
        template = SMSTemplate.objects.get(code=template_code)
    except SMSTemplate.DoesNotExist:
        raise Exception(f"Template {template_code} not found")
    message = template.content
    for key, value in context.items():
        message = message.replace(f"{{{{{key}}}}}", str(value))

    # استفاده از Celery برای ارسال غیرهمزمان
    from .tasks import send_sms_task
    send_sms_task.delay(phone, message, provider.id if provider else None, template.id)