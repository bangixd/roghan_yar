import logging
from celery import shared_task
from django.utils import timezone
from sms.models import SMSLog, UserSMSConfig
from users.models import User

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