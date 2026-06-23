import random
from django.utils import timezone
from datetime import timedelta
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User, OTP
from users.serializers import SendOTPSerializer, VerifyOTPSerializer

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
        return Response({'message': 'کد تأیید ارسال شد', 'code': code})  # در پروداکشن code برگردانده نشود


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
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