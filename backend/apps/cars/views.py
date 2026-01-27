"""
Views for cars app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from apps.cars.models import Car
from apps.cars.serializers import CarSerializer
from apps.vehicles.models import DetectedVehicle


class CarViewSet(viewsets.ModelViewSet):
    """ViewSet for Car model."""
    
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    parser_classes = (MultiPartParser, FormParser)

    @action(detail=False, methods=['get'])
    def with_analysis(self, request):
        """Get all cars with analysis (detected vehicles count)."""
        cars = self.get_queryset()
        data = []
        
        for car in cars:
            car_data = CarSerializer(car).data
            # Add vehicle count
            vehicle_count = DetectedVehicle.objects.filter(video_id=car.id).count()
            car_data['vehicle_count'] = vehicle_count
            data.append(car_data)
        
        return Response(data)

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark a car as paid."""
        car = self.get_object()
        car.paid = True
        car.save()
        return Response(
            {'status': 'success', 'message': 'Car marked as paid'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def mark_unpaid(self, request, pk=None):
        """Mark a car as unpaid."""
        car = self.get_object()
        car.paid = False
        car.save()
        return Response(
            {'status': 'success', 'message': 'Car marked as unpaid'},
            status=status.HTTP_200_OK
        )
