from django.urls import path
from users.views import SendOTPView, VerifyOTPView, ProfileView, SMSConfigView

urlpatterns = [
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/sms-config/', SMSConfigView.as_view(), name='sms-config'),
]