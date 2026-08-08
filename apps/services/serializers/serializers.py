from rest_framework import serializers
from services.models import Service


class ServiceSerializer(serializers.ModelSerializer):
    customer_phone = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()   # (اختیاری) نام مشتری هم نمایش داده شود

    class Meta:
        model = Service
        fields = '__all__'
        read_only_fields = ['performed_by', 'created_at', 'updated_at', 'survey_sent']

    def get_customer_phone(self, obj):
        return obj.customer.phone_number if obj.customer else None

    def get_customer_name(self, obj):
        return obj.customer.full_name if obj.customer else None

    def create(self, validated_data):
        validated_data['performed_by'] = self.context['request'].user
        return super().create(validated_data)