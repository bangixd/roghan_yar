from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای مدل Notification.

    فقط فیلدهای قابل خواندن را در خروجی نمایش می‌دهد.
    """
    class Meta:
        model = Notification
        fields = ['id', 'title', 'body', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']