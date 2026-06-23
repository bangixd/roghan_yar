from django.db import models
from users.models import User


class Customer(models.Model):
    phone_number = models.CharField(max_length=15, unique=True, db_index=True)
    full_name = models.CharField(max_length=200)
    car_model = models.CharField(max_length=100)          # مثلاً پراید، پژو ۲۰۶
    car_usage_type = models.CharField(max_length=50, blank=True, null=True)  # شهری، جاده‌ای، ترکیبی
    birthday = models.DateField(blank=True, null=True)    # جدید: برای تبریک تولد
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='customers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"