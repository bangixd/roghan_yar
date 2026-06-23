from rest_framework import serializers
from tickets.models import Ticket

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'subject', 'message', 'contact_phone', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']  # کاربر فقط پیام جدید می‌دهد، ادمین وضعیت را تغییر می‌دهد

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)