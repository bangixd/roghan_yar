from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from services.models import Service
from customers.models import Customer

class DashboardSummaryView(APIView):
    """
    ارائهٔ خلاصهٔ داشبورد شامل درآمد روز، ماه و سال.

    Endpoint:
        GET /api/v1/dashboard/summary/

    Permissions:
        IsAuthenticated
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # فیلتر مالکیت
        if user.is_staff:
            service_filter = Q()
            customer_filter = Q()
        else:
            service_filter = Q(performed_by=user)
            customer_filter = Q(created_by=user)

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # شروع سال جاری (سال شمسی را می‌توان بر اساس تقویم فارسی تنظیم کرد؛ اینجا میلادی است)
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        # --- کوئری‌های تجمیعی ---
        daily_income = Service.objects.filter(
            service_filter,
            service_date__gte=today_start,
            service_date__lt=today_start + timedelta(days=1)
        ).aggregate(total=Sum('amount'))['total'] or 0

        daily_services = Service.objects.filter(
            service_filter,
            service_date__gte=today_start,
            service_date__lt=today_start + timedelta(days=1)
        ).count()

        total_customers = Customer.objects.filter(customer_filter).count()
        new_customers_this_month = Customer.objects.filter(
            customer_filter,
            created_at__gte=month_start
        ).count()

        monthly_services = Service.objects.filter(
            service_filter,
            service_date__gte=month_start
        ).count()

        monthly_income = Service.objects.filter(
            service_filter,
            service_date__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0

        # درآمد سالانه (از ابتدای سال میلادی تا الان)
        yearly_income = Service.objects.filter(
            service_filter,
            service_date__gte=year_start
        ).aggregate(total=Sum('amount'))['total'] or 0

        data = {
            'daily_income': daily_income,
            'daily_services': daily_services,
            'total_customers': total_customers,
            'new_customers_this_month': new_customers_this_month,
            'monthly_services': monthly_services,
            'monthly_income': monthly_income,
            'yearly_income': yearly_income,          # جدید
        }
        return Response(data)


class MonthlyIncomeReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_staff:
            service_filter = Q()
        else:
            service_filter = Q(performed_by=user)

        # سال مورد نظر (می‌تواند پارامتر باشد، اینجا سال جاری میلادی)
        year = timezone.now().year
        from django.db.models.functions import TruncMonth

        monthly = Service.objects.filter(
            service_filter,
            service_date__year=year
        ).annotate(month=TruncMonth('service_date')).values('month').annotate(
            income=Sum('amount')
        ).order_by('month')

        # تبدیل به دیکشنری ماه‌ها
        result = {}
        for entry in monthly:
            month_name = entry['month'].strftime('%B')  # نام ماه میلادی
            result[month_name] = entry['income']

        total = sum(entry['income'] for entry in monthly)
        return Response({
            'year': year,
            'monthly_income': result,
            'total_yearly_income': total
        })