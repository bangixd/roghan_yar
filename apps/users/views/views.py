import random
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User, OTP
from users.serializers import SendOTPSerializer, VerifyOTPSerializer
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.serializers import UserProfileSerializer, UserSMSConfigSerializer
from sms.models import UserSMSConfig
from users.utils import KavenegarClient
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    نمایش و ویرایش پروفایل کاربر جاری.

    Endpoints:
        GET  /api/v1/profile/
        PUT  /api/v1/profile/
        PATCH /api/v1/profile/
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class SMSConfigView(APIView):
    """
    مدیریت تنظیمات پیامکی کاربر (ایجاد یا بروزرسانی).

    Endpoints:
        GET   /api/v1/profile/sms-config/
        PUT   /api/v1/profile/sms-config/
        PATCH /api/v1/profile/sms-config/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            config = request.user.sms_config
            serializer = UserSMSConfigSerializer(config)
            return Response(serializer.data)
        except UserSMSConfig.DoesNotExist:
            return Response({'detail': 'تنظیمات پیامکی وجود ندارد'}, status=404)

    def put(self, request):
        config, created = UserSMSConfig.objects.get_or_create(user=request.user)
        serializer = UserSMSConfigSerializer(config, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def patch(self, request):
        try:
            config = request.user.sms_config
        except UserSMSConfig.DoesNotExist:
            return Response({'detail': 'تنظیمات وجود ندارد، از PUT استفاده کنید'}, status=404)
        serializer = UserSMSConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone_number']

        # در محیط واقعی کد را از طریق SMS بفرست. فعلاً برای تست برمی‌گردانیم
        code = str(random.randint(1000, 9999))
        expires_at = timezone.now() + timedelta(seconds=120)
        OTP.objects.create(phone_number=phone, code=code, expires_at=expires_at)

        # اینجا سرویس پیامک رو صدا می‌زنی
        client = KavenegarClient()
        message = f'{code}'
        try:
            success, status, message = client.send_sms(phone, message)
        except Exception as e:
            logger.error(f"ارسال OTP به {phone} ناموفق بود: {e}")
            # در محیط توسعه، کد را در پاسخ برگردان (اختیاری)
            if settings.DEBUG:
                return Response({'message': 'کد تأیید (توسعه)', 'code': code})
            return Response(
                {'error': 'خطا در ارسال پیامک. لطفاً دوباره تلاش کنید.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response({'message': 'کد تأیید ارسال شد', 'code': code})  # در پروداکشن code برگردانده نشود


class VerifyOTPView(APIView):
    """
    تأیید کد یکبارمصرف و بازگشت توکن JWT.

    این view کد OTP ارسال‌شده به شماره موبایل را اعتبارسنجی کرده،
    کاربر را یافته یا ایجاد می‌کند و access/refresh token برمی‌گرداند.

    Methods:
        post: دریافت شماره موبایل و کد، احراز هویت و بازگشت توکن.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        پردازش درخواست POST برای تأیید OTP.

        Args:
            request: درخواست DRF شامل فیلدهای phone_number و code.

        Returns:
            Response: شامل access_token و refresh_token در صورت موفقیت،
                      یا پیغام خطا با کد ۴۰۰.

        Raises:
            ValidationError: اگر شماره یا کد ارسال نشده باشد.
        """
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone_number']
        code = serializer.validated_data['code']

        # پیدا کردن آخرین OTP معتبر
        otp = OTP.objects.filter(
            phone_number=phone,
            code=code,
            used=False,
            expires_at__gt=timezone.now()
        ).order_by('-created_at').first()

        if not otp:
            return Response({'error': 'کد نامعتبر یا منقضی شده'}, status=status.HTTP_400_BAD_REQUEST)

        otp.used = True
        otp.save()

        # ساخت یا دریافت کاربر
        user, created = User.objects.get_or_create(phone_number=phone)
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'phone_number': user.phone_number
        })