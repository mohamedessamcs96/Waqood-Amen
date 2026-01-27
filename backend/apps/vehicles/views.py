"""
Views for vehicles app with image enhancement support.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.base import ContentFile
from django.conf import settings
import cv2
import numpy as np
import os
import logging
from apps.vehicles.models import DetectedVehicle
from apps.vehicles.serializers import DetectedVehicleSerializer
from apps.cars.models import Car
from utils.image_enhancement import PlateImageEnhancer

logger = logging.getLogger(__name__)


class DetectedVehicleViewSet(viewsets.ModelViewSet):
    """ViewSet for DetectedVehicle model with image enhancement."""
    
    queryset = DetectedVehicle.objects.all()
    serializer_class = DetectedVehicleSerializer
    parser_classes = (MultiPartParser, FormParser)
    filterset_fields = ['video_id', 'plate_text', 'car_color']

    @action(detail=True, methods=['post'])
    def enhance_plate(self, request, pk=None):
        """
        Enhance plate image using CLAHE and denoising.
        
        Query parameters:
            - method: 'basic' (default) or 'advanced'
            - save: 'true' to save enhanced image back to vehicle
        """
        vehicle = self.get_object()
        
        if not vehicle.plate_image:
            return Response(
                {'error': 'Vehicle has no plate image'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Read plate image
            plate_path = os.path.join(
                settings.MEDIA_ROOT, 
                str(vehicle.plate_image)
            )
            
            if not os.path.exists(plate_path):
                logger.error(f"Plate image not found: {plate_path}")
                return Response(
                    {'error': f'Plate image file not found: {plate_path}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Read image
            image = cv2.imread(plate_path)
            if image is None:
                return Response(
                    {'error': 'Failed to read plate image'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Determine enhancement method
            method = request.query_params.get('method', 'basic')
            
            if method == 'advanced':
                result = PlateImageEnhancer.enhance_advanced(image)
                if not result:
                    return Response(
                        {'error': 'Enhancement failed'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Use the enhanced (CLAHE) version for best results
                enhanced = result.get('enhanced', image)
            else:
                # Basic enhancement (default)
                enhanced = PlateImageEnhancer.enhance_basic(image)
                if enhanced is None:
                    return Response(
                        {'error': 'Enhancement failed'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Optionally save the enhanced image
            should_save = request.query_params.get('save', 'false').lower() == 'true'
            if should_save:
                # Save enhanced image back
                success = cv2.imwrite(plate_path, enhanced)
                if success:
                    logger.info(f"Enhanced plate image saved: {plate_path}")
                    return Response(
                        {
                            'status': 'success',
                            'message': 'Plate image enhanced and saved',
                            'vehicle_id': vehicle.id,
                            'method': method
                        },
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {'error': 'Failed to save enhanced image'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Return enhanced image as response (for preview)
            _, buffer = cv2.imencode('.jpg', enhanced)
            response_data = {
                'status': 'success',
                'message': 'Enhancement preview generated',
                'vehicle_id': vehicle.id,
                'method': method,
                'note': 'Use ?save=true to persist the enhancement'
            }
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error enhancing plate image: {e}")
            return Response(
                {'error': f'Enhancement error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def enhance_all_images(self, request, pk=None):
        """
        Enhance all images for a vehicle (crop, plate, face).
        
        Query parameters:
            - save: 'true' to save enhanced images
        """
        vehicle = self.get_object()
        
        try:
            results = {
                'crop': {'enhanced': False},
                'plate': {'enhanced': False},
                'face': {'enhanced': False},
            }
            
            should_save = request.query_params.get('save', 'false').lower() == 'true'
            
            # Enhance crop image
            if vehicle.crop_image:
                try:
                    crop_path = os.path.join(
                        settings.MEDIA_ROOT,
                        str(vehicle.crop_image)
                    )
                    if os.path.exists(crop_path):
                        image = cv2.imread(crop_path)
                        if image is not None:
                            enhanced = PlateImageEnhancer.enhance_basic(image)
                            if should_save and enhanced is not None:
                                cv2.imwrite(crop_path, enhanced)
                                results['crop']['enhanced'] = True
                except Exception as e:
                    logger.warning(f"Error enhancing crop image: {e}")
            
            # Enhance plate image
            if vehicle.plate_image:
                try:
                    plate_path = os.path.join(
                        settings.MEDIA_ROOT,
                        str(vehicle.plate_image)
                    )
                    if os.path.exists(plate_path):
                        image = cv2.imread(plate_path)
                        if image is not None:
                            enhanced = PlateImageEnhancer.enhance_basic(image)
                            if should_save and enhanced is not None:
                                cv2.imwrite(plate_path, enhanced)
                                results['plate']['enhanced'] = True
                except Exception as e:
                    logger.warning(f"Error enhancing plate image: {e}")
            
            # Enhance face image
            if vehicle.driver_face_image:
                try:
                    face_path = os.path.join(
                        settings.MEDIA_ROOT,
                        str(vehicle.driver_face_image)
                    )
                    if os.path.exists(face_path):
                        image = cv2.imread(face_path)
                        if image is not None:
                            enhanced = PlateImageEnhancer.enhance_basic(image)
                            if should_save and enhanced is not None:
                                cv2.imwrite(face_path, enhanced)
                                results['face']['enhanced'] = True
                except Exception as e:
                    logger.warning(f"Error enhancing face image: {e}")
            
            return Response(
                {
                    'status': 'success',
                    'vehicle_id': vehicle.id,
                    'results': results,
                    'saved': should_save
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"Error enhancing all images: {e}")
            return Response(
                {'error': f'Enhancement error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['put'])
    def update_plate(self, request, pk=None):
        """Update plate text for a detected vehicle."""
        vehicle = self.get_object()
        new_plate = request.data.get('plate_text')
        
        if new_plate:
            vehicle.plate_text = new_plate
            vehicle.save()
            return Response(
                {'status': 'success', 'plate_text': vehicle.plate_text},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {'error': 'plate_text is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def by_video(self, request):
        """Get all vehicles for a specific video/car."""
        video_id = request.query_params.get('video_id')
        
        if not video_id:
            return Response(
                {'error': 'video_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vehicles = DetectedVehicle.objects.filter(video_id=video_id)
        serializer = self.get_serializer(vehicles, many=True)
        return Response(serializer.data)

