from django.db import models
from customers.models import Customer
from services.models import Service

class Feedback(models.Model):
    """
    بازخورد ثبت‌شده توسط مشتری از طریق صفحهٔ نظرسنجی.

    Attributes:
        customer: مشتری (در صورت تطابق شماره).
        service: سرویس مرتبط (اختیاری).
        phone_number: شماره موبایل مشتری (اجباری برای شناسایی).
        rating: امتیاز از ۱ تا ۵.
        comment: نظر متنی.
        created_at: تاریخ ثبت.
    """
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='feedbacks'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='feedbacks'
    )
    phone_number = models.CharField(max_length=15)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} - {self.rating}⭐"