from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from customers.models import Customer
from sms.models import UserSMSConfig
from sms.services import send_sms
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'ارسال پیامک فصلی (تابستان/زمستان)'

    def handle(self, *args, **options):
        today = date.today()
        seasonal_code = None
        if today.month == 4 and today.day == 1:
            seasonal_code = 'seasonal_summer'
        elif today.month == 8 and today.day == 1:
            seasonal_code = 'seasonal_winter'
        if not seasonal_code:
            return

        configs = UserSMSConfig.objects.filter(
            is_active=True,
            seasonal_enabled=True
        ).select_related('user')

        for config in configs:
            user = config.user
            customers = Customer.objects.filter(created_by=user)
            for cust in customers:
                try:
                    send_sms(user, cust.phone_number, seasonal_code, {'name': cust.full_name})
                except Exception as e:
                    logger.error(f"Seasonal SMS failed: {e}")