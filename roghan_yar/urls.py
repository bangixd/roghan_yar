from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from customers.views import CustomerViewSet
from services.views import ServiceViewSet
from users.views import SendOTPView, VerifyOTPView

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'services', ServiceViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('api/v1/auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
]