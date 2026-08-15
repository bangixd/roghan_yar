from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from services.models import Service
from sms.services import send_sms
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'ارسال پیامک یادآوری سرویس (۳ روز مانده)'

    def handle(self, *args, **options):
        today = timezone.now().date()
        upcoming = Service.objects.filter(
            next_service_date=today + timedelta(days=3),
            performed_by__isnull=False
        ).select_related('customer', 'performed_by')

        for srv in upcoming:
            user = srv.performed_by
            if not user or not hasattr(user, 'sms_config') or not user.sms_config.reminder_enabled:
                continue
            try:
                send_sms(user, srv.customer.phone_number, 'reminder', {
                    'name': srv.customer.full_name,
                    'next_date': srv.next_service_date
                })
            except Exception as e:
                logger.error(f"Reminder SMS failed: {e}")