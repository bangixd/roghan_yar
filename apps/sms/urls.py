from django.urls import path, include
from rest_framework.routers import DefaultRouter
from sms.views import CampaignViewSet, SMSLogViewSet, SMSTemplateViewSet, BulkSMSView

router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet)
router.register(r'logs', SMSLogViewSet)
router.register(r'templates', SMSTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('bulk-send/', BulkSMSView.as_view(), name='bulk-send'),
]