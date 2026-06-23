from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from tickets.models import Ticket
from tickets.serializers import TicketSerializer

class TicketViewSet(viewsets.ModelViewSet):
    """
    مدیریت تیکت‌های پشتیبانی (ایجاد، مشاهده، بروزرسانی).

    کاربران می‌توانند تیکت جدید ایجاد کنند و تیکت‌های خود را ببینند.
    فقط کاربر مالک تیکت می‌تواند آن را به‌روزرسانی یا حذف کند.
    ادمین‌ها می‌توانند وضعیت تیکت را تغییر دهند.

    Endpoints:
        GET    /api/v1/tickets/          - لیست تیکت‌های کاربر جاری
        POST   /api/v1/tickets/          - ایجاد تیکت جدید
        GET    /api/v1/tickets/{id}/     - جزئیات یک تیکت
        PUT    /api/v1/tickets/{id}/     - بروزرسانی کامل تیکت
        PATCH  /api/v1/tickets/{id}/     - بروزرسانی جزئی (مثلاً تغییر وضعیت توسط ادمین)
        DELETE /api/v1/tickets/{id}/     - حذف تیکت

    Authentication:
        JWT (Bearer token)

    Permissions:
        IsAuthenticated, و بررسی مالکیت در سطح object.
    """
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['subject', 'message']
    ordering_fields = ['created_at']

    def get_queryset(self):
        """
        فیلتر کوئری برای نمایش فقط تیکت‌های کاربر جاری (به‌جز ادمین که همه را ببیند).

        Returns:
            QuerySet: تیکت‌های فیلترشده.
        """
        if self.request.user.is_staff:
            return Ticket.objects.all()
        return Ticket.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        هنگام ایجاد تیکت، کاربر را به‌طور خودکار تنظیم کن.

        Args:
            serializer: نمونهٔ TicketSerializer.

        Returns:
            None
        """
        serializer.save(user=self.request.user)