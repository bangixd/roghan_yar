from rest_framework import viewsets, permissions, filters
from .models import Feedback
from .serializers import FeedbackSerializer

class FeedbackViewSet(viewsets.ReadOnlyModelViewSet):
    """
    مشاهدهٔ نظرات مشتریان.

    کاربر احراز هویت‌شده فقط نظرات مشتریان خود را می‌بیند.
    ادمین همه را می‌بیند.

    Endpoints:
        GET /api/v1/feedback/       - لیست نظرات
        GET /api/v1/feedback/{id}/  - جزئیات یک نظر
    """
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['phone_number', 'comment']
    ordering_fields = ['created_at', 'rating']
    queryset = Feedback.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Feedback.objects.select_related('customer').all()
        # کاربران عادی فقط نظرات مشتریان خود را ببینند
        # (با استفاده از رابطه مشتری ← created_by)
        return Feedback.objects.filter(
            customer__created_by=user
        ).select_related('customer')