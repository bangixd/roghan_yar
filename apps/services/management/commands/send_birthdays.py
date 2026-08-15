from django.core.management.base import BaseCommand
from django.utils import timezone
from customers.models import Customer
from sms.services import send_sms
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'ارسال پیامک تبریک تولد'

    def handle(self, *args, **options):
        today = timezone.now().date()
        customers = Customer.objects.filter(
            birthday__day=today.day, birthday__month=today.month
        ).select_related('created_by')

        for cust in customers:
            user = cust.created_by
            if not user or not hasattr(user, 'sms_config') or not user.sms_config.birthday_enabled:
                continue
            try:
                send_sms(user, cust.phone_number, 'birthday', {'name': cust.full_name})
            except Exception as e:
                logger.error(f"Birthday SMS failed: {e}")