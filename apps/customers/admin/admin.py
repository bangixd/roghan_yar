from customers.models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'full_name', 'car_model', 'created_at']
    search_fields = ['phone_number', 'full_name']