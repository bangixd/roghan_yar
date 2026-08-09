from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from notifications.models import Notification
from notifications.serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    مدیریت اعلان‌های کاربر (لیست، جزئیات، بروزرسانی).

    کاربر می‌تواند فقط اعلان‌های خود را ببیند.
    عملیات اضافی:
        - mark_read: یک اعلان خاص را خوانده‌شده کند.
        - mark_all_read: تمام اعلان‌های خوانده‌نشدهٔ کاربر را خوانده‌شده کند.

    Endpoints:
        GET    /api/v1/notifications/              - لیست اعلان‌ها
        GET    /api/v1/notifications/{id}/         - جزئیات یک اعلان
        PATCH  /api/v1/notifications/{id}/         - بروزرسانی (مثلاً تغییر is_read به‌صورت دستی)
        POST   /api/v1/notifications/{id}/mark-read/       - نشان‌کردن یک اعلان به‌عنوان خوانده‌شده
        POST   /api/v1/notifications/mark-all-read/        - خوانده‌شده کردن همه اعلان‌ها

    Authentication:
        JWT (Bearer token)

    Permissions:
        IsAuthenticated, کاربر فقط به اعلان‌های خود دسترسی دارد.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['created_at']
    search_fields = ['title', 'body']
    queryset = Notification.objects.all()

    def perform_create(self, serializer):
        """
        هنگام ایجاد نوتیفیکیشن، کاربر جاری را به‌عنوان صاحب نوتیفیکیشن تنظیم کن.
        """
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """
        فقط اعلان‌های کاربر احراز هویت‌شده را برگردان.

        Returns:
            QuerySet: اعلان‌های متعلق به request.user.
        """
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        یک اعلان خاص را به‌عنوان خوانده‌شده علامت‌گذاری کن.

        Args:
            pk (str): شناسهٔ اعلان.

        Returns:
            Response: پیام تأیید یا خطا.
        """
        notification = self.get_object()
        if notification.is_read:
            return Response({'detail': 'قبلاً خوانده شده'}, status=200)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'detail': 'اعلان با موفقیت خوانده شد.'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        تمام اعلان‌های خوانده‌نشدهٔ کاربر جاری را یک‌جا خوانده‌شده کن.

        Returns:
            Response: تعداد اعلان‌های به‌روزرسانی‌شده.
        """
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'detail': f'{updated} اعلان خوانده شد.'})