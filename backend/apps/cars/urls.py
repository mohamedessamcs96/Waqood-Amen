"""
URL configuration for cars app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.cars.views import CarViewSet

router = DefaultRouter()
router.register(r'cars', CarViewSet, basename='car')

urlpatterns = [
    path('', include(router.urls)),
    # Legacy endpoints for compatibility
    path('cars-with-analysis/', CarViewSet.as_view({'get': 'with_analysis'}), name='cars-with-analysis'),
]
