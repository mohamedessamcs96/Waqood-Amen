"""
Cars app models for Gas Station Monitoring system.
"""
from django.db import models


class Car(models.Model):
    """Car model to store car information and payment status."""
    
    plate = models.CharField(max_length=20, unique=True, db_index=True)
    paid = models.BooleanField(default=False, db_index=True)
    video = models.CharField(max_length=255, null=True, blank=True)
    analysis = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cars'
        ordering = ['-created_at']

    def __str__(self):
        return f"Car {self.id} - Plate: {self.plate} - Paid: {self.paid}"
