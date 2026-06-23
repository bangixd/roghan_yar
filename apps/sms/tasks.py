import logging
from sms.models import SMSLog, UserSMSConfig
from users.models import User
from celery import shared_task
from django.utils import timezone
from sms.models import Campaign, CampaignRecipient
from customers.models import Customer

logger = logging.getLogger(__name__)


def _get_backend(provider_name: str, api_key: str, sender: str):
    """
    یک نمونه از بک‌اند پیامکی مناسب را بر اساس نام پروایدر برمی‌گرداند.

    Args:
        provider_name: نام پروایدر (مثلاً 'kavenegar' یا 'melipayamak').
        api_key: کلید API کاربر.
        sender: شماره فرستنده.

    Returns:
        یک شیء از نوع BaseSMSBackend.

    Raises:
        ValueError: اگر پروایدر پشتیبانی نشود.
    """
    # در اینجا می‌توانیم با یک دیکشنری یا منطق شرطی بک‌اندها را انتخاب کنیم
    if provider_name == 'kavenegar':
        from sms.services import KavenegarBackend  # فرض بر این که این کلاس را داریم
        return KavenegarBackend(api_key=api_key, sender=sender)
    elif provider_name == 'melipayamak':
        # نمونه برای ملی‌پیامک
        from sms.services import MeliPayamakBackend
        return MeliPayamakBackend(api_key=api_key, sender=sender)
    else:
        raise ValueError(f"پروایدر '{provider_name}' پشتیبانی نمی‌شود")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_task(self, phone: str, message: str, provider_name: str,
                  api_key: str, sender: str, user_id: int = None,
                  template_id: int = None):
    """
    تسک Celery برای ارسال یک پیامک از طریق پروایدر مشخص و ثبت لاگ.

    این تسک پیامک را با استفاده از تنظیمات کاربر (api_key, provider_name, sender)
    ارسال می‌کند و نتیجه را در مدل SMSLog ذخیره می‌کند. در صورت خطا،
    تا ۳ بار تلاش مجدد می‌کند.

    Args:
        phone: شماره تلفن مقصد.
        message: متن پیامک نهایی (جایگذاری قالب قبلاً انجام شده).
        provider_name: نام پروایدر انتخابی کاربر (مثلاً 'kavenegar').
        api_key: کلید API کاربر در سامانهٔ پیامکی.
        sender: شمارهٔ فرستنده.
        user_id: شناسهٔ کاربری که پیامک از طرف او ارسال می‌شود (اختیاری).
        template_id: شناسهٔ قالب استفاده‌شده (اختیاری).

    Returns:
        dict: اطلاعات وضعیت ارسال (در صورت موفقیت).

    Raises:
        Retry: در صورت خطا، تلاش مجدد می‌کند.
    """
    # ۱. ایجاد لاگ اولیه
    log = SMSLog.objects.create(
        user_id=user_id,
        provider_name=provider_name,
        template_id=template_id,
        receiver_phone=phone,
        message=message,
        status='pending'
    )

    try:
        # ۲. دریافت بک‌اند مناسب و ارسال
        backend = _get_backend(provider_name, api_key, sender)
        response = backend.send(phone, message)

        # ۳. به‌روزرسانی لاگ با موفقیت
        log.status = 'sent'
        log.response_data = response
        log.sent_at = timezone.now()
        log.save(update_fields=['status', 'response_data', 'sent_at'])

        logger.info(f"SMS sent to {phone} via {provider_name}")

        return {'status': 'sent', 'log_id': log.id}

    except Exception as exc:
        # ۴. ثبت خطا و تلاش مجدد
        log.status = 'failed'
        log.retry_count = self.request.retries + 1
        log.response_data = {'error': str(exc)}
        log.save(update_fields=['status', 'retry_count', 'response_data'])

        logger.error(f"SMS failed to {phone}: {exc}")

        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1)
def process_campaign(self, campaign_id):
    """
    پردازش یک کمپین: ساخت لیست مخاطبین و ارسال پیامک‌ها.

    بر اساس target_type کمپین:
        - all: همه مشتریان کاربر
        - filtered: مشتریان مطابق با فیلتر JSON
        - manual: مخاطبین دستی (باید قبلاً اضافه شده باشند یا همزمان ایجاد شوند)

    Args:
        campaign_id: شناسهٔ کمپین.
    """
    try:
        campaign = Campaign.objects.select_related('user').get(id=campaign_id)
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        return

    if campaign.status != Campaign.Status.PROCESSING:
        return

    user = campaign.user

    # --- ساخت لیست مخاطبین ---
    if campaign.target_type == Campaign.TargetType.ALL:
        customers = Customer.objects.filter(created_by=user)
        for cust in customers:
            CampaignRecipient.objects.get_or_create(
                campaign=campaign,
                phone_number=cust.phone_number,
                defaults={'customer': cust}
            )
    elif campaign.target_type == Campaign.TargetType.FILTERED:
        filters = campaign.filters
        qs = Customer.objects.filter(created_by=user)
        # نمونه فیلترها: car_model, last_service_before, etc.
        if 'car_model' in filters:
            qs = qs.filter(car_model=filters['car_model'])
        if 'last_service_before' in filters:
            from datetime import datetime
            date_limit = datetime.strptime(filters['last_service_before'], '%Y-%m-%d').date()
            # مشتریانی که سرویس آخرشان قبل از این تاریخ است
            from services.models import Service
            qs = qs.filter(services__service_date__lt=date_limit).distinct()
        # می‌توان فیلترهای دیگر را اضافه کرد
        for cust in qs:
            CampaignRecipient.objects.get_or_create(
                campaign=campaign,
                phone_number=cust.phone_number,
                defaults={'customer': cust}
            )
    elif campaign.target_type == Campaign.TargetType.MANUAL:
        # فرض می‌کنیم مخاطبین دستی از قبل توسط کاربر اضافه شده‌اند (از طریق API دیگر)
        # در غیر این‌صورت هیچ کاری نمی‌کنیم.
        pass

    # --- ارسال پیامک‌ها ---
    recipients = campaign.recipients.filter(sent=False)
    total = recipients.count()
    if total == 0:
        campaign.status = Campaign.Status.COMPLETED
        campaign.save(update_fields=['status'])
        return f"Campaign {campaign.id} completed with 0 recipients."

    # ارسال پیامک‌ها با Celery (چانک‌بندی برای حجم بالا)
    chunk_size = 50
    recipient_ids = list(recipients.values_list('id', flat=True))
    for i in range(0, len(recipient_ids), chunk_size):
        chunk = recipient_ids[i:i+chunk_size]
        send_campaign_chunk.delay(campaign.id, chunk)

    campaign.status = Campaign.Status.PROCESSING  # همچنان در حال ارسال
    campaign.save(update_fields=['status'])
    return f"Campaign {campaign.id} processing started for {total} recipients."

@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_campaign_chunk(self, campaign_id, recipient_ids):
    """
    ارسال پیامک برای یک دسته (chunk) از مخاطبین کمپین.

    Args:
        campaign_id: شناسه کمپین.
        recipient_ids: لیست شناسه‌های CampaignRecipient.
    """
    from .services import get_user_sms_config, send_sms_task  # یا send_sms
    try:
        campaign = Campaign.objects.select_related('user').get(id=campaign_id)
    except Campaign.DoesNotExist:
        return

    user = campaign.user
    try:
        config = get_user_sms_config(user)
    except ValueError:
        # اگر تنظیمات پیامکی معتبر نباشد، خطا را ثبت و متوقف شو
        logger.error(f"Invalid SMS config for user {user.id}")
        return

    template = campaign.template
    message_text = campaign.message or (template.content if template else '')

    for rec_id in recipient_ids:
        try:
            recipient = CampaignRecipient.objects.select_related('customer').get(id=rec_id, campaign=campaign)
        except CampaignRecipient.DoesNotExist:
            continue

        # جایگزاری متغیرها در قالب (اگر قالب باشد)
        context = {}
        if recipient.customer:
            context = {
                'name': recipient.customer.full_name,
                'car_model': recipient.customer.car_model
            }
        final_message = message_text
        for key, value in context.items():
            final_message = final_message.replace(f"{{{{{key}}}}}", str(value))

        # ارسال پیامک
        send_sms_task.delay(
            phone=recipient.phone_number,
            message=final_message,
            provider_name=config.provider_name,
            api_key=config.api_key,
            sender=config.sender_number,
            user_id=user.id,
            template_id=template.id if template else None
        )
        # علامت‌گذاری به‌عنوان ارسال‌شده
        recipient.sent = True
        recipient.sent_at = timezone.now()
        recipient.save(update_fields=['sent', 'sent_at'])

    # بررسی پایان کار کمپین
    remaining = CampaignRecipient.objects.filter(campaign=campaign, sent=False).count()
    if remaining == 0:
        campaign.status = Campaign.Status.COMPLETED
        campaign.save(update_fields=['status'])

@shared_task
def process_scheduled_campaigns():
    """
    کمپین‌های با وضعیت scheduled که زمان ارسال آنها فرا رسیده را پیدا
    و پردازش می‌کند.
    """
    now = timezone.now()
    campaigns = Campaign.objects.filter(
        status=Campaign.Status.SCHEDULED,
        scheduled_at__lte=now
    )
    for campaign in campaigns:
        campaign.status = Campaign.Status.PROCESSING
        campaign.save(update_fields=['status'])
        process_campaign.delay(campaign.id)