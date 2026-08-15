import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from sms.models import SMSLog
from sms.services import get_user_sms_config
from sms.backends import KavenegarBackend, MeliPayamakBackend  # مسیر صحیح بک‌اندها

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'پردازش پیامک‌های در انتظار (pending)'

    def handle(self, *args, **options):
        logs = SMSLog.objects.filter(status='pending').order_by('created_at')[:100]
        for log in logs:
            try:
                if not log.user or not hasattr(log.user, 'sms_config') or not log.user.sms_config.is_active:
                    log.status = 'failed'
                    log.response_data = {'error': 'تنظیمات کاربر غیرفعال است'}
                    log.save(update_fields=['status', 'response_data'])
                    continue

                config = log.user.sms_config
                if config.provider_name == 'kavenegar':
                    backend = KavenegarBackend(config.api_key, config.sender_number)
                elif config.provider_name == 'melipayamak':
                    backend = MeliPayamakBackend(config.api_key, config.sender_number)
                else:
                    raise ValueError(f"پروایدر نامعتبر: {config.provider_name}")

                response = backend.send(log.receiver_phone, log.message)
                log.status = 'sent'
                log.response_data = response
                log.sent_at = timezone.now()
                log.save(update_fields=['status', 'response_data', 'sent_at'])
                logger.info(f"SMS sent to {log.receiver_phone}")
            except Exception as e:
                log.status = 'failed'
                log.response_data = {'error': str(e)}
                log.save(update_fields=['status', 'response_data'])
                logger.error(f"SMS failed to {log.receiver_phone}: {e}")