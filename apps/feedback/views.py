from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from .models import Feedback
from .serializers import FeedbackSerializer, FeedbackSubmitSerializer
from customers.models import Customer


class FeedbackViewSet(viewsets.ModelViewSet):
    """
    مدیریت نظرات مشتریان (ثبت عمومی + مشاهده، جزئیات و حذف برای کاربر).

    عملیات‌ها:
        POST   /api/v1/feedback/        - ثبت نظر جدید (عمومی، بدون احراز هویت)
        GET    /api/v1/feedback/        - لیست نظرات (کاربر احراز هویت‌شده؛ فقط مشتریان خودش)
        GET    /api/v1/feedback/{id}/   - جزئیات یک نظر (احراز هویت‌شده، با محدودیت مالکیت)
        DELETE /api/v1/feedback/{id}/   - حذف یک نظر (احراز هویت‌شده، با محدودیت مالکیت)

    Permissions:
        - ثبت: AllowAny
        - سایر: IsAuthenticated + فیلتر مالکیت
    """
    queryset = Feedback.objects.select_related('customer').all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['phone_number', 'comment']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """برای ثبت از سریالایزر ساده و برای نمایش از سریالایزر کامل استفاده کن."""
        if self.action == 'create':
            return FeedbackSubmitSerializer
        return FeedbackSerializer

    def get_permissions(self):
        """
        ثبت نظر برای همه آزاد است؛ سایر عملیات نیاز به احراز هویت دارند.
        """
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        کاربران عادی فقط نظرات مشتریان خود را ببینند، ادمین همه را.
        """
        qs = super().get_queryset()
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            qs = qs.filter(customer__created_by=self.request.user)
        return qs

    def create(self, request, *args, **kwargs):
        """
        ثبت بازخورد جدید (عمومی).

        در صورت وجود شماره تلفن در جدول مشتریان، رابطهٔ customer نیز تنظیم می‌شود.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone_number']
        rating = serializer.validated_data['rating']
        comment = serializer.validated_data.get('comment', '')

        # اتصال به مشتری در صورت وجود
        customer = Customer.objects.filter(phone_number=phone).first()

        feedback = Feedback.objects.create(
            phone_number=phone,
            rating=rating,
            comment=comment,
            customer=customer
        )

        return Response(
            {
                'message': 'نظر شما با موفقیت ثبت شد. متشکریم!',
                'id': feedback.id,
                'created_at': feedback.created_at
            },
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        """
        حذف نظر (فقط توسط مالک یا ادمین).
        """
        feedback = self.get_object()
        # ادمین یا کاربری که مشتری متعلق به اوست
        if not request.user.is_staff and feedback.customer and feedback.customer.created_by != request.user:
            return Response(
                {'error': 'شما اجازه حذف این نظر را ندارید.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)