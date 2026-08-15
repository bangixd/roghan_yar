# sms/backends.py
import requests

class BaseSMSBackend:
    def send(self, phone, message):
        raise NotImplementedError

class KavenegarBackend(BaseSMSBackend):
    def __init__(self, api_key, sender):
        self.api_key = api_key
        self.sender = sender

    def send(self, phone, message):
        # پیاده‌سازی واقعی با requests
        # این یک نمونه ساده است
        url = "https://api.kavenegar.com/v1/{}/sms/send.json".format(self.api_key)
        payload = {
            "receptor": phone,
            "message": message,
            "sender": self.sender
        }
        # response = requests.post(url, data=payload)
        # return response.json()
        # فعلاً برای تست، چاپ می‌کنیم
        print(f"Sending SMS to {phone}: {message} (via Kavenegar)")
        return {"status": "sent", "message": "OK"}

class MeliPayamakBackend(BaseSMSBackend):
    def __init__(self, api_key, sender):
        self.api_key = api_key
        self.sender = sender

    def send(self, phone, message):
        # پیاده‌سازی ملی‌پیامک
        print(f"Sending SMS to {phone}: {message} (via MeliPayamak)")
        return {"status": "sent", "message": "OK"}