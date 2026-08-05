from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from services.models import Service
from customers.models import Customer


class DashboardSummaryView(APIView):
    """
    ارائهٔ خلاصهٔ داشبورد برای کاربر جاری.

    این ویو اطلاعات آماری زیر را برمی‌گرداند:
        - daily_income: مجموع مبلغ سرویس‌های امروز.
        - daily_services: تعداد سرویس‌های امروز.
        - total_customers: تعداد کل مشتریان کاربر.
        - new_customers_this_month: تعداد مشتریان جدید در ماه جاری.
        - monthly_services: تعداد سرویس‌های ثبت‌شده در ماه جاری.
        - monthly_income: مجموع درآمد سرویس‌های ماه جاری.

    کاربران عادی فقط داده‌های مربوط به خود را می‌بینند،
    ادمین‌ها آمار کل سیستم را مشاهده می‌کنند.

    Endpoint:
        GET /api/v1/dashboard/summary/

    Authentication:
        JWT (Bearer token)

    Permissions:
        IsAuthenticated
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # پایهٔ فیلترهای مالکیت
        if user.is_staff:
            service_filter = Q()
            customer_filter = Q()
        else:
            service_filter = Q(performed_by=user)
            customer_filter = Q(created_by=user)

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # --- کوئری‌های تجمیعی ---
        # درآمد امروز
        daily_income = Service.objects.filter(
            service_filter,
            service_date__gte=today_start,
            service_date__lt=today_start + timedelta(days=1)
        ).aggregate(total=Sum('amount'))['total'] or 0

        # تعداد سرویس‌های امروز
        daily_services = Service.objects.filter(
            service_filter,
            service_date__gte=today_start,
            service_date__lt=today_start + timedelta(days=1)
        ).count()

        # تعداد کل مشتریان
        total_customers = Customer.objects.filter(customer_filter).count()

        # مشتریان جدید این ماه (created_at >= اول ماه)
        new_customers_this_month = Customer.objects.filter(
            customer_filter,
            created_at__gte=month_start
        ).count()

        # تعداد سرویس‌های این ماه
        monthly_services = Service.objects.filter(
            service_filter,
            service_date__gte=month_start
        ).count()

        # درآمد این ماه
        monthly_income = Service.objects.filter(
            service_filter,
            service_date__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0

        data = {
            'daily_income': daily_income,
            'daily_services': daily_services,
            'total_customers': total_customers,
            'new_customers_this_month': new_customers_this_month,
            'monthly_services': monthly_services,
            'monthly_income': monthly_income,
        }
        return Response(data)