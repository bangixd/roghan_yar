from django.contrib import admin
from sms.models import Campaign, CampaignRecipient, SMSLog, SMSTemplate, UserSMSConfig, SMSProvider


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'target_type', 'status', 'scheduled_at']
    list_filter = ['status', 'target_type']

@admin.register(CampaignRecipient)
class CampaignRecipientAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'phone_number', 'sent']

@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ['receiver_phone', 'status', 'user', 'created_at']
    list_filter = ['status', 'provider']
    search_fields = ['receiver_phone', 'message']

@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    list_display = ['code', 'user', 'created_at']
    search_fields = ['code']

@admin.register(UserSMSConfig)
class UserSMSConfigAdmin(admin.ModelAdmin):
    list_display = ['user', 'provider_name', 'is_active']

@admin.register(SMSProvider)
class SMSProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']