from rest_framework import viewsets
from services.models import Service
from services.serializers import ServiceSerializer

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related('customer').all()
    serializer_class = ServiceSerializer
    filterset_fields = ['customer', 'service_date', 'next_service_date']
    search_fields = ['customer__full_name', 'customer__phone_number']