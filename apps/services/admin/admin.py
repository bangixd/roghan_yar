from django.contrib import admin
from services.models import Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['customer', 'service_date', 'amount', 'next_service_date', 'survey_sent']
    list_filter = ['service_date', 'next_service_date']