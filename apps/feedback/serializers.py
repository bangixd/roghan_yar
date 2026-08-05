from rest_framework import serializers
from .models import Feedback

class FeedbackSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    class Meta:
        model = Feedback
        fields = ['id', 'phone_number', 'customer_name', 'rating', 'comment', 'created_at']