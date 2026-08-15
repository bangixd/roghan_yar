from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from services.models import Service
from sms.services import send_sms
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'ارسال پیامک نظرسنجی (۱ روز بعد از سرویس)'

    def handle(self, *args, **options):
        yesterday = timezone.now() - timedelta(days=1)
        services = Service.objects.filter(
            service_date__date=yesterday.date(),
            survey_sent=False
        ).select_related('customer', 'performed_by')

        for srv in services:
            user = srv.performed_by
            if not user or not hasattr(user, 'sms_config') or not user.sms_config.survey_enabled:
                continue
            try:
                send_sms(user, srv.customer.phone_number, 'survey', {
                    'name': srv.customer.full_name,
                    'phone': srv.customer.phone_number,
                    'service_id': srv.id
                })
                srv.survey_sent = True
                srv.save(update_fields=['survey_sent'])
            except Exception as e:
                logger.error(f"Survey SMS failed: {e}")