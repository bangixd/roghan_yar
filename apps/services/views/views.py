from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from services.models import Service
from services.serializers import ServiceSerializer
from notifications.services import create_notification


class ServiceViewSet(viewsets.ModelViewSet):
    """
    مدیریت کامل سرویس‌های تعویض روغن (ایجاد، خواندن، بروزرسانی، حذف).

    این ViewSet عملیات CRUD را برای مدل Service فراهم می‌کند.
    کاربر باید احراز هویت شده باشد. فیلد performed_by هنگام ایجاد به‌طور
    خودکار تنظیم می‌شود. کوئری‌ها به‌صورت بهینه با select_related
    روی customer بارگذاری می‌شوند.

    ویژگی‌ها:
        - فیلترپذیری بر اساس customer، service_date، next_service_date.
        - جستجو روی نام و شماره مشتری (از طریق رابطه).
        - مرتب‌سازی بر اساس service_date نزولی.

    Endpoints:
        GET    /api/v1/services/          - لیست سرویس‌ها
        POST   /api/v1/services/          - ثبت سرویس جدید
        GET    /api/v1/services/{id}/     - جزئیات یک سرویس
        PUT    /api/v1/services/{id}/     - بروزرسانی کامل سرویس
        PATCH  /api/v1/services/{id}/     - بروزرسانی جزئی
        DELETE /api/v1/services/{id}/     - حذف سرویس

    Authentication:
        JWT (Bearer token)

    Permissions:
        IsAuthenticated
    """
    queryset = Service.objects.select_related('customer').all().order_by('-service_date')
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['customer', 'service_date', 'next_service_date']
    search_fields = ['customer__full_name', 'customer__phone_number']
    ordering_fields = ['service_date', 'amount']

    def perform_create(self, serializer):
        """
        هنگام ثبت سرویس جدید، کاربر انجام‌دهنده را به‌طور خودکار تنظیم کن.

        Args:
            serializer: نمونهٔ ServiceSerializer با داده‌های معتبر.

        Returns:
            None
        """
        service = serializer.save(performed_by=self.request.user)
        create_notification(
            user=self.request.user,
            title="سرویس جدید ثبت شد",
            body=f"سرویس برای {service.customer.full_name} در تاریخ {service.service_date.strftime('%Y-%m-%d')} ثبت گردید."
        )
        serializer.save(performed_by=self.request.user)