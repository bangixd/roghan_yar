from django.db import models
from customers.models import Customer
from users.models import User


class Service(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='services')
    service_date = models.DateTimeField()                  # تاریخ انجام سرویس
    current_mileage = models.IntegerField()                # کیلومتر فعلی
    next_mileage = models.IntegerField()                   # کیلومتر تعویض بعدی
    next_service_date = models.DateField(blank=True, null=True)  # تاریخ پیشنهادی بعدی
    amount = models.DecimalField(max_digits=10, decimal_places=0)  # مبلغ کل
    items = models.TextField(blank=True, null=True)       # شرح خدمات (می‌تونه JSON هم باشه)
    notes = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='services_done')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # فیلدهای مربوط به پیامک‌های خودکار
    survey_sent = models.BooleanField(default=False)      # نظرسنجی فرستاده شده؟

    def __str__(self):
        return f"{self.customer.full_name} - {self.service_date.strftime('%Y-%m-%d')}"