"""
Vehicles app models for detected vehicles and analysis.
"""
from django.db import models
from apps.cars.models import Car


class DetectedVehicle(models.Model):
    """Model to store detected vehicles from video analysis."""
    
    video_id = models.IntegerField(db_index=True)  # References Car.id
    vehicle_index = models.IntegerField(default=0)
    crop_image = models.CharField(max_length=255, null=True, blank=True)
    plate_image = models.CharField(max_length=255, null=True, blank=True)
    plate_text = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    car_color = models.CharField(max_length=50, null=True, blank=True)
    driver_face_image = models.CharField(max_length=255, null=True, blank=True)
    vehicle_confidence = models.FloatField(default=0.0)
    plate_confidence = models.FloatField(null=True, blank=True)
    face_confidence = models.FloatField(null=True, blank=True)
    timestamp = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'detected_vehicles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['video_id']),
            models.Index(fields=['plate_text']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Vehicle {self.id} - Video {self.video_id} - Plate: {self.plate_text}"
