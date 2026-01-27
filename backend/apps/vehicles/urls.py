"""
URL configuration for vehicles app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.vehicles.views import DetectedVehicleViewSet

router = DefaultRouter()
router.register(r'detected-vehicles', DetectedVehicleViewSet, basename='detected-vehicle')

urlpatterns = [
    path('', include(router.urls)),
]
