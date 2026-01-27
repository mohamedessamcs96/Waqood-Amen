"""
Serializers for cars app.
"""
from rest_framework import serializers
from apps.cars.models import Car


class CarSerializer(serializers.ModelSerializer):
    """Serializer for Car model."""
    
    class Meta:
        model = Car
        fields = ['id', 'plate', 'paid', 'video', 'analysis', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
