from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from customers.views import CustomerViewSet
from services.views import ServiceViewSet
from users.views import SendOTPView, VerifyOTPView, ProfileView, SMSConfigView
from tickets.views import TicketViewSet
from notifications.views import NotificationViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from feedback.views import FeedbackViewSet



router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'tickets', TicketViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'feedback', FeedbackViewSet)



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api/v1/dashboard/', include('dashboard.urls')),
    path('api/v1/sms/', include('sms.urls')),
    path('api/v1/profile/', ProfileView.as_view(), name='profile'),
    path('api/v1/profile/sms-config/', SMSConfigView.as_view(), name='sms-config'),
    path('api/v1/auth/send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('api/v1/auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),

    # OpenAPI schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # ReDoc (اختیاری)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
