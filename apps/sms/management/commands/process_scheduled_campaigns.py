from django.core.management.base import BaseCommand
from django.utils import timezone
from sms.models import Campaign
from sms.services import process_campaign_logic  # باید این تابع را در services.py پیاده کنید
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'اجرای کمپین‌های زمان‌بندی‌شده'

    def handle(self, *args, **options):
        now = timezone.now()
        campaigns = Campaign.objects.filter(
            status=Campaign.Status.SCHEDULED,
            scheduled_at__lte=now
        )
        for campaign in campaigns:
            campaign.status = Campaign.Status.PROCESSING
            campaign.save(update_fields=['status'])
            try:
                process_campaign_logic(campaign)
            except Exception as e:
                logger.error(f"Campaign processing failed: {e}")
                campaign.status = Campaign.Status.DRAFT  # یا failed
                campaign.save(update_fields=['status'])