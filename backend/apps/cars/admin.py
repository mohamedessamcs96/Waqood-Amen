"""
Admin configuration for cars and vehicles.
"""
from django.contrib import admin
from apps.cars.models import Car
from apps.vehicles.models import DetectedVehicle


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['id', 'plate', 'paid', 'created_at', 'updated_at']
    list_filter = ['paid', 'created_at']
    search_fields = ['plate']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('plate', 'paid', 'video')
        }),
        ('Analysis', {
            'fields': ('analysis',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DetectedVehicle)
class DetectedVehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'video_id', 'plate_text', 'car_color', 'vehicle_confidence', 'created_at']
    list_filter = ['car_color', 'vehicle_confidence', 'created_at']
    search_fields = ['plate_text', 'video_id']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('video_id', 'vehicle_index', 'timestamp')
        }),
        ('Images', {
            'fields': ('crop_image', 'plate_image', 'driver_face_image')
        }),
        ('Detection Data', {
            'fields': ('plate_text', 'car_color', 'vehicle_confidence', 'plate_confidence', 'face_confidence')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
