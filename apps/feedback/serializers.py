from rest_framework import serializers
from .models import Feedback

class FeedbackSubmitSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)
    service_id = serializers.IntegerField(required=False, allow_null=True)

class FeedbackSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone_number', read_only=True)
    service_id = serializers.IntegerField(source='service.id', read_only=True, allow_null=True)
    service_date = serializers.DateTimeField(source='service.service_date', read_only=True, allow_null=True)
    service_description = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            'id', 'phone_number', 'customer_name', 'customer_phone',
            'rating', 'comment', 'created_at',
            'service_id', 'service_date', 'service_description'
        ]

    def get_service_description(self, obj):
        if obj.service:
            return f"سرویس {obj.service.service_date.strftime('%Y-%m-%d')} - {obj.service.items or 'بدون شرح'}"
        return None