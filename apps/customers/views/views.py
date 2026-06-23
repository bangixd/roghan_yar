from rest_framework import viewsets
from customers.models import Customer
from customers.serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filterset_fields = ['phone_number', 'full_name', 'car_model']
    search_fields = ['phone_number', 'full_name']