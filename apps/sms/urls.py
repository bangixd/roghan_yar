from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampaignViewSet, SMSLogViewSet, SMSTemplateViewSet

router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet)
router.register(r'logs', SMSLogViewSet)
router.register(r'templates', SMSTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]