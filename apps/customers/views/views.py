from rest_framework import viewsets, permissions, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from customers.models import Customer
from customers.serializers import CustomerSerializer
from notifications.services import create_notification
import io
from datetime import datetime
from openpyxl import load_workbook
from rest_framework.decorators import action
from rest_framework.response import Response


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


    @action(detail=False, methods=['post'], url_path='upload-excel')
    def upload_excel(self, request):
        """
        بارگذاری فایل اکسل و ایجاد گروهی مشتریان.

        ستون‌های مورد انتظار (فقط دو ستون):
            - phone_number (اجباری)
            - full_name (اختیاری، می‌تواند خالی باشد)

        سایر ستون‌ها نادیده گرفته می‌شوند.

        شماره‌های تکراری برای کاربر جاری نادیده گرفته می‌شوند.
        """
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'فایلی ارسال نشده است.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not file_obj.name.endswith(('.xlsx', '.xls')):
            return Response(
                {'error': 'فقط فایل‌های Excel با پسوند xlsx یا xls پذیرفته می‌شوند.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            wb = load_workbook(filename=io.BytesIO(file_obj.read()))
            ws = wb.active
        except Exception as e:
            return Response(
                {'error': f'خطا در خواندن فایل: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # خواندن سرستون‌ها
        headers = [cell.value for cell in ws[1]]
        phone_idx = None
        name_idx = None

        # تشخیص ستون شماره تلفن و نام
        for i, h in enumerate(headers):
            if h is None:
                continue
            header = str(h).strip().lower()
            if header in ['phone_number', 'phone', 'mobile', 'شماره', 'تلفن', 'موبایل']:
                phone_idx = i
            elif header in ['full_name', 'name', 'نام', 'نام مشتری', 'نام و نام خانوادگی']:
                name_idx = i

        if phone_idx is None:
            return Response(
                {'error': 'ستون شماره تلفن (phone_number) یافت نشد.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_count = 0
        errors = []

        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            # اطمینان از اینکه ردیف خالی نباشد
            if not row or len(row) <= phone_idx or not row[phone_idx]:
                continue

            phone = str(row[phone_idx]).strip()
            full_name = str(row[name_idx]).strip() if name_idx is not None and row[name_idx] else ''

            # جلوگیری از تکراری بودن
            if Customer.objects.filter(phone_number=phone, created_by=request.user).exists():
                errors.append(f'ردیف {row_idx}: شماره {phone} قبلاً ثبت شده است.')
                continue

            Customer.objects.create(
                phone_number=phone,
                full_name=full_name,
                created_by=request.user
            )
            created_count += 1

        return Response(
            {
                'created_count': created_count,
                'errors': errors
            },
            status=status.HTTP_200_OK
        )