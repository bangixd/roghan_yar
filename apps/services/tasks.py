# import logging
# from celery import shared_task
# from django.utils import timezone
# from datetime import timedelta
# from datetime import date
# from customers.models import Customer
# from services.models import Service
# from sms.services import send_sms
# from sms.models import UserSMSConfig
# from sms.models import SMSLog
#
#
# logger = logging.getLogger(__name__)
#
# @shared_task
# def send_birthday_greetings():
#     today = timezone.now().date()
#     birthdays = Customer.objects.filter(birthday__day=today.day, birthday__month=today.month)
#     for customer in birthdays:
#         send_sms(customer.phone_number, 'birthday', {'name': customer.full_name})
#
# @shared_task
# def send_post_service_survey():
#     yesterday = timezone.now() - timedelta(days=1)
#     services = Service.objects.filter(
#         service_date__date=yesterday.date(),
#         survey_sent=False
#     ).select_related('customer', 'performed_by')  # کاهش کوئری
#
#     for service in services:
#         user = service.performed_by
#         if not user or not hasattr(user, 'sms_config') or not user.sms_config.survey_enabled:
#             continue   # کاربر معتبر نیست یا نظرسنجی را غیرفعال کرده
#
#         try:
#             send_sms(
#                 user=user,
#                 phone=service.customer.phone_number,
#                 template_code='survey',
#                 context={
#                     'name': service.customer.full_name,
#                     'service_date': service.service_date.strftime('%Y-%m-%d'),
#                     'survey_link': 'https://yourdomain.com/survey/',  # آدرس صفحه نظرسنجی
#                     'service_id': service.id,
#                     'phone': service.customer.phone_number  # برای پیش‌فرض در فرم
#                 }
#             )
#             service.survey_sent = True
#             service.save(update_fields=['survey_sent'])
#         except Exception as e:
#             logger.error(f"Survey SMS failed for service {service.id}: {e}")
#
# @shared_task
# def send_service_reminders():
#     today = timezone.now().date()
#     # سرویس‌هایی که تاریخ بعدی‌شون امروز یا ۳ روز دیگه‌ست
#     upcoming = Service.objects.filter(
#         next_service_date__isnull=False,
#         next_service_date=today + timedelta(days=3)  # یا هر بازه‌ای که می‌خوای
#     )
#     for service in upcoming:
#         send_sms(
#             service.customer.phone_number,
#             'reminder',
#             {
#                 'name': service.customer.full_name,
#                 'next_date': service.next_service_date.strftime('%Y-%m-%d')
#             }
#         )
#
#
# @shared_task
# def send_seasonal_reminders():
#     """
#     بررسی تاریخ فعلی و ارسال پیامک فصلی به مشتریان کاربران فعال.
#     اجرا: روزانه (اما منطق درون آن چک می‌کند که آیا امروز تاریخ شروع فصل است).
#     """
#     today = date.today()
#     # تاریخ‌های شروع فصل (قابل تنظیم)
#     SUMMER_START_MONTH, SUMMER_START_DAY = 4, 1   # ۱ اردیبهشت
#     WINTER_START_MONTH, WINTER_START_DAY = 8, 1   # ۱ آبان
#
#     seasonal_code = None
#     if today.month == SUMMER_START_MONTH and today.day == SUMMER_START_DAY:
#         seasonal_code = 'seasonal_summer'
#     elif today.month == WINTER_START_MONTH and today.day == WINTER_START_DAY:
#         seasonal_code = 'seasonal_winter'
#     else:
#         return  # امروز شروع فصل نیست
#
#     # دریافت کاربرانی که seasonal_enabled=True دارند و تنظیمات کلی فعال است
#     active_configs = UserSMSConfig.objects.filter(
#         is_active=True,
#         seasonal_enabled=True
#     ).select_related('user')
#
#     for config in active_configs:
#         user = config.user
#         # مشتریانی که توسط این کاربر ثبت شده‌اند
#         customers = Customer.objects.filter(created_by=user)
#         for customer in customers:
#             try:
#                 send_sms(
#                     user=user,
#                     phone=customer.phone_number,
#                     template_code=seasonal_code,
#                     context={'name': customer.full_name}
#                 )
#             except Exception as e:
#                 # لاگ خطا
#                 pass
#
# @shared_task
# def send_retention_messages():
#     """
#     بررسی روزانه مشتریان هر کاربر و ارسال پیامک بر اساس مدت زمان گذشته از آخرین سرویس.
#     """
#     today = timezone.now().date()
#     active_configs = UserSMSConfig.objects.filter(
#         is_active=True,
#         retention_enabled=True
#     ).select_related('user')
#
#     for config in active_configs:
#         user = config.user
#         # گرفتن تمام مشتریان کاربر
#         customers = Customer.objects.filter(created_by=user)
#         for customer in customers:
#             # آخرین سرویس مشتری
#             last_service = customer.services.order_by('-service_date').first()
#             if not last_service:
#                 continue
#             days_since_last = (today - last_service.service_date.date()).days
#
#             template_code = None
#             if days_since_last == 30:
#                 template_code = 'retention_30'
#             elif days_since_last == 45:
#                 template_code = 'retention_45'
#             elif days_since_last == 90:
#                 template_code = 'retention_90'
#
#             if template_code:
#                 already_sent = SMSLog.objects.filter(
#                     receiver_phone=customer.phone_number,
#                     user=user,
#                     template__code=template_code,
#                     created_at__gte=timezone.now() - timedelta(days=1)  # همان روز
#                 ).exists()
#                 if not already_sent:
#                     try:
#                         send_sms(
#                             user=user,
#                             phone=customer.phone_number,
#                             template_code=template_code,
#                             context={
#                                 'name': customer.full_name,
#                                 'days': days_since_last
#                             }
#                         )
#                     except Exception as e:
#                         pass