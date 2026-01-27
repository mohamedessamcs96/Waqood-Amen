"""
Serializers for vehicles app.
"""
from rest_framework import serializers
from apps.vehicles.models import DetectedVehicle


class DetectedVehicleSerializer(serializers.ModelSerializer):
    """Serializer for DetectedVehicle model."""
    
    class Meta:
        model = DetectedVehicle
        fields = [
            'id', 'video_id', 'vehicle_index', 'crop_image', 'plate_image',
            'plate_text', 'car_color', 'driver_face_image', 'vehicle_confidence',
            'plate_confidence', 'face_confidence', 'timestamp', 'created_at'
        ]
        read_only_fields = ['created_at']
