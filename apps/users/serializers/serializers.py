from rest_framework import serializers
from users.models import User
from sms.models import UserSMSConfig


class UserSMSConfigSerializer(serializers.ModelSerializer):
    """
    سریالایزر تنظیمات پیامکی کاربر.

    ویژگی‌ها:
        - فیلد user شماره موبایل کاربر را (از طریق __str__) نمایش می‌دهد و فقط‌خواندنی است.
        - فیلد api_key فقط در درخواست‌های نوشتن (write_only) قابل ارسال است و در پاسخ‌ها نمایش داده نمی‌شود.
        - فیلدهای created_at و updated_at نیز فقط‌خواندنی هستند.
    """
    user = serializers.StringRelatedField(read_only=True)   # نمایش شماره موبایل کاربر

    class Meta:
        model = UserSMSConfig
        fields = '__all__'
        extra_kwargs = {
            'api_key': {'write_only': True},       # کلید API هرگز در خروجی نمایش داده نشود
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class UserProfileSerializer(serializers.ModelSerializer):
    sms_config = UserSMSConfigSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'phone_number', 'full_name', 'sms_config']
        read_only_fields = ['id', 'phone_number']


class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6)