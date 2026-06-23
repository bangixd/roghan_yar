from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from customers.models import Customer
from services.models import Service
from sms.services import send_sms

@shared_task
def send_birthday_greetings():
    today = timezone.now().date()
    birthdays = Customer.objects.filter(birthday__day=today.day, birthday__month=today.month)
    for customer in birthdays:
        send_sms(customer.phone_number, 'birthday', {'name': customer.full_name})

@shared_task
def send_post_service_survey():
    # مثلاً ۱ روز بعد از سرویس
    target_date = timezone.now() - timedelta(days=1)
    services = Service.objects.filter(
        service_date__date=target_date.date(),
        survey_sent=False
    )
    for service in services:
        send_sms(
            service.customer.phone_number,
            'survey',
            {
                'name': service.customer.full_name,
                'service_date': service.service_date.strftime('%Y-%m-%d'),
                'survey_link': 'https://example.com/survey/123'  # می‌تونه از تنظیمات بیاد
            }
        )
        service.survey_sent = True
        service.save(update_fields=['survey_sent'])

@shared_task
def send_service_reminders():
    today = timezone.now().date()
    # سرویس‌هایی که تاریخ بعدی‌شون امروز یا ۳ روز دیگه‌ست
    upcoming = Service.objects.filter(
        next_service_date__isnull=False,
        next_service_date=today + timedelta(days=3)  # یا هر بازه‌ای که می‌خوای
    )
    for service in upcoming:
        send_sms(
            service.customer.phone_number,
            'reminder',
            {
                'name': service.customer.full_name,
                'next_date': service.next_service_date.strftime('%Y-%m-%d')
            }
        )