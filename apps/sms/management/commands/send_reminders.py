# مشابه تسک قبلی، اما مستقیماً send_sms() را صدا می‌زند تا در صف قرار گیرد
from django.core.management.base import BaseCommand
from services.tasks import send_service_reminders_logic  # منطق را از تسک قبلی استخراج کنید

class Command(BaseCommand):
    help = 'ارسال پیامک یادآوری سرویس'

    def handle(self, *args, **options):
        send_service_reminders_logic()