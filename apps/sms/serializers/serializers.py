from rest_framework import serializers
from sms.models import Campaign, CampaignRecipient, SMSLog, SMSTemplate, UserSMSConfig

class SMSTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSTemplate
        fields = ['id', 'code', 'content', 'user']
        read_only_fields = ['user']

class CampaignRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignRecipient
        fields = ['id', 'customer', 'phone_number', 'sent', 'sent_at']
        read_only_fields = ['sent', 'sent_at']

class CampaignSerializer(serializers.ModelSerializer):
    recipients_count = serializers.SerializerMethodField()
    sent_count = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'target_type', 'filters', 'scheduled_at',
            'template', 'message', 'status', 'created_at', 'updated_at',
            'recipients_count', 'sent_count'
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']

    def get_recipients_count(self, obj):
        return obj.recipients.count()

    def get_sent_count(self, obj):
        return obj.recipients.filter(sent=True).count()

class SMSLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSLog
        fields = ['id', 'provider', 'receiver_phone', 'message', 'status', 'created_at', 'sent_at']
        read_only_fields = ['id', 'created_at', 'sent_at']

class BulkSMSRequestSerializer(serializers.Serializer):
    phones = serializers.ListField(
        child=serializers.CharField(max_length=15),
        allow_empty=False,
        help_text="لیست شماره تلفن‌های مقصد"
    )
    message = serializers.CharField(help_text="متن پیامک")