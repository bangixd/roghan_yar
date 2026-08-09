from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from customers.models import Customer
from customers.serializers import CustomerSerializer
from notifications.services import create_notification



class CustomerViewSet(viewsets.ModelViewSet):
    """
    مدیریت کامل مشتریان (ایجاد، خواندن، بروزرسانی، حذف).

    این ViewSet تمام عملیات CRUD را برای مدل Customer فراهم می‌کند.
    کاربر احراز هویت‌شده باید باشد. هنگام ایجاد، فیلد created_by به‌طور
    خودکار با کاربر درخواست‌دهنده پر می‌شود.

    ویژگی‌ها:
        - فیلترپذیری بر اساس phone_number, full_name, car_model.
        - جستجوی متنی روی phone_number و full_name.
        - مرتب‌سازی پیش‌فرض بر اساس created_at نزولی.

    Endpoints:
        GET    /api/v1/customers/          - لیست مشتریان (با صفحه‌بندی)
        POST   /api/v1/customers/          - ایجاد مشتری جدید
        GET    /api/v1/customers/{id}/     - نمایش جزئیات یک مشتری
        PUT    /api/v1/customers/{id}/     - بروزرسانی کامل یک مشتری
        PATCH  /api/v1/customers/{id}/     - بروزرسانی جزئی یک مشتری
        DELETE /api/v1/customers/{id}/     - حذف یک مشتری

    Authentication:
        JWT (Bearer token)

    Permissions:
        IsAuthenticated
    """
    queryset = Customer.objects.all().order_by('-created_at')
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['phone_number', 'full_name', 'car_model']
    search_fields = ['phone_number', 'full_name']
    ordering_fields = ['created_at', 'full_name']

    def perform_create(self, serializer):
        """
        هنگام ایجاد مشتری، کاربر ایجادکننده را به‌طور خودکار ثبت کن.

        Args:
            serializer: نمونهٔ CustomerSerializer با داده‌های معتبر.

        Returns:
            None
        """
        customer = serializer.save(created_by=self.request.user)
        create_notification(
            user=self.request.user,
            title="مشتری جدید",
            body=f"مشتری {customer.full_name} با شماره {customer.phone_number} با موفقیت ثبت شد."
        )
        serializer.save(created_by=self.request.user)
