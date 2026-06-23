from .models import UserSMSConfig, SMSTemplate, SMSLog
from .tasks import send_sms_task


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


def send_sms(user, phone, template_code, context=None):
    """
    ارسال پیامک از طرف یک کاربر خاص.

    Args:
        user: کاربری که پیامک از حساب او فرستاده می‌شود.
        phone: شماره مقصد.
        template_code: کد قالب (مثلاً 'welcome').
        context: دیکشنری مقادیر برای جایگذاری در قالب.

    Returns:
        نتیجهٔ ارسال (غیرهمزمان با Celery).
    """
    if context is None:
        context = {}
    config = get_user_sms_config(user)

    # اولویت با قالب سفارشی کاربر، در غیر این صورت قالب سیستمی
    template = SMSTemplate.objects.filter(code=template_code, user=user).first()
    if not template:
        template = SMSTemplate.objects.filter(code=template_code, user__isnull=True).first()
    if not template:
        raise Exception(f"قالب '{template_code}' یافت نشد")

    message = template.content
    for key, value in context.items():
        message = message.replace(f"{{{{{key}}}}}", str(value))

    # ارسال از طریق Celery (با پارامترهای کاربر)
    send_sms_task.delay(
        phone=phone,
        message=message,
        provider_name=config.provider_name,
        api_key=config.api_key,
        sender=config.sender_number,
        user_id=user.id,
        template_id=template.id
    )