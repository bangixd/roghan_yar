from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Service
from sms.services import send_sms
import logging


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Service)
def send_welcome_on_first_service(sender, instance, created, **kwargs):
    """
    اگر سرویس تازه ایجاد شده و اولین سرویس مشتری باشد،
    پیامک خوش‌آمدگویی از طرف کاربر ثبت‌کننده ارسال شود.
    """
    if created:
        customer = instance.customer
        # بررسی کنیم که تعداد سرویس‌های این مشتری دقیقاً ۱ باشد
        if customer.services.count() == 1:
            user = instance.performed_by  # کاربری که سرویس را ثبت کرده
            if user and hasattr(user, 'sms_config') and user.sms_config.welcome_enabled:
                try:
                    send_sms(
                        user=user,
                        phone=customer.phone_number,
                        template_code='welcome',
                        context={'name': customer.full_name, 'car_model': customer.car_model}
                    )
                except Exception as e:
                    logger.warning(f"Could not send welcome SMS: {e}")