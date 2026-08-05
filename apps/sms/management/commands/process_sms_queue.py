from django.core.management.base import BaseCommand
from sms.models import SMSLog
from sms.services import _get_backend  # تابع کمکی برای بک‌اند پیامک
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'پردازش پیامک‌های در صف (pending) و ارسال آن‌ها'

    def handle(self, *args, **options):
        pending_logs = SMSLog.objects.filter(status='pending').order_by('created_at')[:50]  # دسته‌ای
        for log in pending_logs:
            try:
                # اطلاعات کاربر از log.user (باید sms_config داشته باشد)
                user_config = log.user.sms_config
                if not user_config.is_active:
                    log.status = 'failed'
                    log.response_data = {'error': 'تنظیمات پیامک کاربر غیرفعال است'}
                    log.save()
                    continue
                backend = _get_backend(user_config.provider_name, user_config.api_key, user_config.sender_number)
                response = backend.send(log.receiver_phone, log.message)
                log.status = 'sent'
                log.response_data = response
                log.sent_at = timezone.now()
                log.save()
                logger.info(f"SMS sent to {log.receiver_phone}")
            except Exception as e:
                log.status = 'failed'
                log.response_data = {'error': str(e)}
                log.save()
                logger.error(f"SMS failed: {e}")