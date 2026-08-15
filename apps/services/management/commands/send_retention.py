from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from customers.models import Customer
from sms.models import UserSMSConfig, SMSLog
from sms.services import send_sms
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'ارسال پیامک عدم مراجعه (۶۰ و ۹۰ روز)'

    def handle(self, *args, **options):
        today = timezone.now().date()
        configs = UserSMSConfig.objects.filter(
            is_active=True,
            retention_enabled=True
        ).select_related('user')

        for config in configs:
            user = config.user
            customers = Customer.objects.filter(created_by=user)
            for cust in customers:
                last_service = cust.services.order_by('-service_date').first()
                if not last_service:
                    continue
                days_since = (today - last_service.service_date.date()).days
                template_code = None
                if days_since == 60:
                    template_code = 'retention_60'
                elif days_since == 90:
                    template_code = 'retention_90'
                else:
                    continue

                # جلوگیری از ارسال تکراری
                already_sent = SMSLog.objects.filter(
                    receiver_phone=cust.phone_number,
                    user=user,
                    template__code=template_code,
                    created_at__gte=today
                ).exists()
                if already_sent:
                    continue
                try:
                    send_sms(user, cust.phone_number, template_code, {'name': cust.full_name})
                except Exception as e:
                    logger.error(f"Retention SMS failed: {e}")