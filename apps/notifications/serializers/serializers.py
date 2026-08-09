from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'body', 'is_read', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']