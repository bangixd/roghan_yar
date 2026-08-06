from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'rating', 'customer', 'created_at']
    list_filter = ['rating']
    search_fields = ['phone_number', 'comment']