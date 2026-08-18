import requests
import zeep
from zeep import Client


class BaseSMSBackend:
    def send(self, phone, message):
        raise NotImplementedError


class ParsGreenBackend:
    """
    بک‌اند پیامکی برای پنل پارس گرین (SOAP).

    این کلاس با استفاده از zeep به WSDL سرویس ارسال پیامک متصل می‌شود
    و متد SendGroupSMS را فراخوانی می‌کند.

    Args:
        api_key: در این سرویس معمولاً استفاده نمی‌شود (بستگی به تنظیمات دارد).
        sender: شماره فرستنده (شماره خط).
    """
    def __init__(self, api_key, sender):
        self.api_key = api_key   # اگر لازم شد از آن استفاده می‌کنیم
        self.sender = sender
        self.client = Client('http://login.parsgreen.com/Api/SendSMS.asmx?WSDL')

    def send(self, phone, message):
        """
        ارسال پیامک تکی از طریق پارس گرین.

        Args:
            phone: شماره گیرنده (مثلاً '09121234567')
            message: متن پیامک

        Returns:
            dict: پاسخ سرویس در صورت موفقیت

        Raises:
            Exception: در صورت خطا
        """
        # طبق مستندات، SendGroupSMS پارامترهای زیر را می‌گیرد:
        # signature, fromNo, toNoArr, txt, isFlash, udh, success, retStr
        # ما از signature خالی، udh خالی و success=0 استفاده می‌کنیم
        # در صورت نیاز به احراز هویت، می‌توانید signature را از api_key تنظیم کنید.
        signature = self.api_key or ""
        to_array = zeep.helpers.serialize_object([phone])
        is_flash = False
        udh = ""
        success = 0
        ret_str = []

        try:
            # فراخوانی متد SendGroupSMS
            result = self.client.service.SendGroupSMS(
                signature,
                self.sender,
                [phone],      # آرایه‌ی شماره‌ها
                message,
                is_flash,
                udh,
                success,
                ret_str
            )
            # معمولاً نتیجه شامل وضعیت ارسال و شناسه پیامک است
            # ساختار دقیق را از پاسخ بررسی کنید
            return {
                'status': 'sent',
                'response': str(result)
            }
        except Exception as e:
            raise Exception(f"ParsGreen send failed: {e}")