from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from sms.models import Campaign, CampaignRecipient, SMSLog, SMSTemplate
from sms.serializers import (
    CampaignSerializer, CampaignRecipientSerializer,
    SMSLogSerializer, SMSTemplateSerializer
)
from sms.tasks import process_campaign
from django.db.models import Q


class CampaignViewSet(viewsets.ModelViewSet):
    """
    مدیریت کمپین‌های پیامکی (ایجاد، ویرایش، حذف، ارسال).

    Endpoints اصلی:
        GET    /api/v1/sms/campaigns/              - لیست کمپین‌ها
        POST   /api/v1/sms/campaigns/              - ایجاد کمپین جدید
        GET    /api/v1/sms/campaigns/{id}/         - جزئیات
        PUT    /api/v1/sms/campaigns/{id}/         - ویرایش کامل
        PATCH  /api/v1/sms/campaigns/{id}/         - ویرایش جزئی
        DELETE /api/v1/sms/campaigns/{id}/         - حذف

    اکشن‌های سفارشی:
        POST /api/v1/sms/campaigns/{id}/send_now/  - ارسال فوری کمپین
        POST /api/v1/sms/campaigns/{id}/duplicate/ - کپی کردن کمپین
    """
    serializer_class = CampaignSerializer
    queryset = Campaign.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'target_type']
    search_fields = ['name']
    ordering_fields = ['created_at', 'scheduled_at']

    def get_queryset(self):
        """
        فقط کمپین‌های کاربر جاری (یا همه برای ادمین).
        """
        if self.request.user.is_staff:
            return Campaign.objects.all()
        return Campaign.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        هنگام ایجاد، کاربر را به‌عنوان صاحب کمپین تنظیم کن.
        """
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def send_now(self, request, pk=None):
        """
        ارسال فوری کمپین (حتی اگر زمان‌بندی داشته باشد).

        وضعیت کمپین به 'processing' تغییر کرده و تسک Celery برای ارسال
        به صف فرستاده می‌شود.
        """
        campaign = self.get_object()
        if campaign.status not in [Campaign.Status.DRAFT, Campaign.Status.SCHEDULED]:
            return Response(
                {'detail': 'کمپین در وضعیتی نیست که بتوان ارسال کرد.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        campaign.status = Campaign.Status.PROCESSING
        campaign.save(update_fields=['status'])
        # فراخوانی تسک پردازش
        process_campaign.delay(campaign.id)
        return Response({'detail': 'کمپین در صف ارسال قرار گرفت.'})

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        یک کپی از کمپین (با وضعیت پیش‌نویس) ایجاد کن.
        """
        original = self.get_object()
        original.pk = None
        original.name = f"{original.name} (کپی)"
        original.status = Campaign.Status.DRAFT
        original.scheduled_at = None
        original.save()
        return Response(CampaignSerializer(original).data, status=status.HTTP_201_CREATED)

class SMSLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    مشاهدهٔ تاریخچهٔ پیامک‌های ارسال‌شده توسط کاربر.

    Endpoints:
        GET /api/v1/sms/logs/       - لیست لاگ‌ها
        GET /api/v1/sms/logs/{id}/  - جزئیات یک لاگ
    """
    serializer_class = SMSLogSerializer
    queryset = SMSLog.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'provider']
    search_fields = ['receiver_phone', 'message']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        if self.request.user.is_staff:
            return SMSLog.objects.all()
        return SMSLog.objects.filter(user=self.request.user)

class SMSTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    مشاهدهٔ قالب‌های پیامکی (پیش‌فرض و سفارشی کاربر).

    کاربران فقط قالب‌های سیستمی و قالب‌های خود را می‌بینند.
    """
    serializer_class = SMSTemplateSerializer
    queryset = SMSTemplate.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'content']

    def get_queryset(self):
        user = self.request.user
        return SMSTemplate.objects.filter(
            Q(user=user) | Q(user__isnull=True)
        )