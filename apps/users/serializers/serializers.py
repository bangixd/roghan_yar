from rest_framework import serializers
from users.models import User
from sms.models import UserSMSConfig


class UserSMSConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSMSConfig
        fields = [
            'provider_name', 'api_key', 'sender_number',
            'welcome_enabled', 'reminder_enabled', 'birthday_enabled',
            'survey_enabled', 'is_active'
        ]
        extra_kwargs = {'api_key': {'write_only': True}}  # امنیتی


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