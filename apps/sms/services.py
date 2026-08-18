from sms.models import UserSMSConfig, SMSTemplate, SMSLog
from sms.backends import ParsGreenBackend
from django.conf import settings


def get_default_backend():
    """
    برمی‌گرداند نمونه‌ای از بک‌اند پیامکی بر اساس تنظیمات پیش‌فرض سیستم.

    تنظیمات مورد نیاز در settings.py:
        DEFAULT_SMS_PROVIDER: نام پروایدر (kavenegar یا melipayamak)
        DEFAULT_SMS_API_KEY: کلید API
        DEFAULT_SMS_SENDER: شماره فرستنده

    Returns:
        یک شیء از کلاس بک‌اند مربوطه

    Raises:
        ValueError: اگر پروایدر پشتیبانی نشود یا تنظیمات ناقص باشد.
    """
    provider_name = getattr(settings, 'DEFAULT_SMS_PROVIDER', '').lower()
    api_key = getattr(settings, 'DEFAULT_SMS_API_KEY', '')
    sender = getattr(settings, 'DEFAULT_SMS_SENDER', '')

    if not provider_name or not api_key:
        raise ValueError("تنظیمات پیامکی پیش‌فرض (DEFAULT_SMS_PROVIDER, DEFAULT_SMS_API_KEY) کامل نیست.")

    if provider_name == 'parsgreen':
        return ParsGreenBackend(api_key=api_key, sender=sender)
    # اگر پروایدرهای دیگری هم دارید، اینجا اضافه کنید
    # elif provider_name == 'kavenegar': ...
    else:
        raise ValueError(f"پروایدر پیش‌فرض '{provider_name}' پشتیبانی نمی‌شود.")

def get_user_sms_config(user):
    """
    دریافت تنظیمات پیامکی کاربر، در صورت عدم وجود، خطا برگردان.
    """
    try:
        config = user.sms_config
        if not config.is_active or not config.api_key:
            raise ValueError("تنظیمات پیامکی کاربر فعال نیست یا کلید API ندارد")
        return config
    except UserSMSConfig.DoesNotExist:
        raise ValueError("تنظیمات پیامکی برای این کاربر یافت نشد")


def send_otp_sms(phone, code):
    backend = get_default_backend()
    message = f"کد تأیید شما: {code}"
    return backend.send(phone, message)


def send_sms(user, phone, template_code, context=None):
    if context is None:
        context = {}
    config = get_user_sms_config(user)  # ممکن است خطا بدهد، در caller مدیریت می‌شود

    template = SMSTemplate.objects.filter(code=template_code, user=user).first()
    if not template:
        template = SMSTemplate.objects.filter(code=template_code, user__isnull=True).first()
    if not template:
        raise Exception(f"قالب '{template_code}' یافت نشد")

    message = template.content
    for key, value in context.items():
        message = message.replace(f"{{{{{key}}}}}", str(value))

    # ایجاد رکورد در صف دیتابیس
    SMSLog.objects.create(
        user=user,
        provider_name=config.provider_name,
        template=template,
        receiver_phone=phone,
        message=message,
        status='pending'
    )


def send_plain_sms(user, phone, message):
    config = get_user_sms_config(user)
    SMSLog.objects.create(
        user=user,
        provider_name=config.provider_name,
        receiver_phone=phone,
        message=message,
        status='pending'
    )
