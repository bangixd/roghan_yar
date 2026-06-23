from django.contrib import admin
from tickets.models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['subject', 'message', 'user__phone_number']