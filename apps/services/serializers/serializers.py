from rest_framework import serializers
from services.models import Service

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'
        read_only_fields = ['performed_by', 'created_at', 'updated_at', 'survey_sent']

    def create(self, validated_data):
        validated_data['performed_by'] = self.context['request'].user
        return super().create(validated_data)