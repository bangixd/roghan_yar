from rest_framework import serializers
from .models import Feedback

class FeedbackSubmitSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)

class FeedbackSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)

    class Meta:
        model = Feedback
        fields = ['id', 'phone_number', 'customer_name', 'rating', 'comment', 'created_at']