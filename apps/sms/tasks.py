from celery import shared_task
from sms.models import SMSProvider, SMSTemplate, SMSLog
from .services import get_active_provider
from django.utils import timezone


@shared_task(bind=True, max_retries=3)
def send_sms_task(self, phone, message, provider_id=None, template_id=None):
    try:
        if provider_id:
            provider = SMSProvider.objects.get(id=provider_id)
        else:
            provider = get_active_provider()

        # فراخوانی سرویس واقعی
        backend = get_active_provider()  # یا مستقیم provider رو بدیم
        response = backend.send(phone, message)
        SMSLog.objects.create(
            provider=provider,
            template_id=template_id,
            receiver_phone=phone,
            message=message,
            status='sent',
            response_data=response,
            sent_at=timezone.now()
        )
    except Exception as e:
        SMSLog.objects.create(
            receiver_phone=phone,
            message=message,
            status='failed',
            response_data={'error': str(e)}
        )
        raise self.retry(exc=e, countdown=60)