from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from .models import Feedback
from .serializers import FeedbackSerializer, FeedbackSubmitSerializer, FeedbackReplySerializer
from customers.models import Customer
from services.models import Service
from rest_framework.decorators import action
from django.utils import timezone
from notifications.services import create_notification



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
        service_id = serializer.validated_data.get('service_id')  # دریافت شناسه سرویس

        # اتصال به مشتری در صورت وجود
        customer = Customer.objects.filter(phone_number=phone).first()

        # یافتن سرویس در صورت ارسال service_id
        service = None
        if service_id:
            try:
                service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                pass  # در صورت نامعتبر بودن، نادیده می‌گیریم

        feedback = Feedback.objects.create(
            phone_number=phone,
            rating=rating,
            comment=comment,
            customer=customer,
            service=service      # اتصال به سرویس

        )
        if feedback.customer and feedback.customer.created_by:
            create_notification(
                user=feedback.customer.created_by,
                title="نظر جدید",
                body=f"مشتری {feedback.customer.full_name} به سرویس امتیاز {feedback.rating} داد."
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

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reply(self, request, pk=None):
        """
        ثبت پاسخ به یک نظر.

        فقط ادمین یا کاربری که مشتری این نظر متعلق به اوست می‌تواند پاسخ دهد.
        """
        feedback = self.get_object()

        # بررسی مالکیت
        if not request.user.is_staff:
            if not feedback.customer or feedback.customer.created_by != request.user:
                return Response(
                    {'error': 'شما اجازه پاسخ به این نظر را ندارید.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = FeedbackReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reply_text = serializer.validated_data['reply']

        feedback.reply = reply_text
        feedback.replied_at = timezone.now()
        feedback.save(update_fields=['reply', 'replied_at'])

        create_notification(
            user=request.user,
            title="پاسخ ثبت شد",
            body=f"پاسخ شما به نظر مشتری {feedback.customer.full_name} با موفقیت ثبت گردید."
        )
        # برگرداندن کل feedback با پاسخ جدید (با استفاده از سریالایزر نمایش)
        output_serializer = FeedbackSerializer(feedback, context={'request': request})
        return Response(output_serializer.data)