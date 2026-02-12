"""
Views for cars app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from apps.cars.models import Car
from apps.cars.serializers import CarSerializer
from apps.vehicles.models import DetectedVehicle
import os
import json
import logging

logger = logging.getLogger(__name__)


def analyze_video_for_car(car):
    """
    Run YOLO analysis on a car's video.
    Detects vehicles, license plates, car color, driver region.
    Saves crops to car_crops/, plate_crops/, face_crops/.
    Creates DetectedVehicle records in DB.
    """
    import cv2
    import numpy as np
    from ultralytics import YOLO

    video_path = f'/app/videos/{car.video}'
    if not os.path.exists(video_path):
        logger.error(f'Video not found: {video_path}')
        return {'error': f'Video not found: {video_path}'}

    logger.info(f'[ANALYZE] Starting analysis for car {car.id}: {video_path}')

    # Load models
    yolo_vehicle = YOLO('/app/yolov8n.pt')
    yolo_license = YOLO('/app/best.pt')

    # Load OCR — PaddleOCR (primary, better Arabic) + EasyOCR (fallback)
    paddle_ocr = None
    try:
        from paddleocr import PaddleOCR
        paddle_ocr = PaddleOCR(use_angle_cls=True, lang='ar', show_log=False, use_gpu=False)
        logger.info('[ANALYZE] PaddleOCR loaded (primary)')
    except Exception:
        logger.warning('[ANALYZE] PaddleOCR not available')

    easyocr_reader = None
    try:
        import easyocr
        easyocr_reader = easyocr.Reader(['en', 'ar'], gpu=False)
        logger.info('[ANALYZE] EasyOCR loaded (fallback)')
    except Exception:
        logger.warning('[ANALYZE] EasyOCR not available')

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {'error': 'Failed to open video'}

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = max(1, int(fps))
    frame_indices = list(range(0, frame_count, frame_interval))

    logger.info(f'[ANALYZE] Video: {frame_count} frames, {fps:.1f} FPS, analyzing {len(frame_indices)} frames')

    # Track unique vehicles by grid position
    unique_vehicles = {}

    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue

        timestamp = frame_idx / fps if fps > 0 else 0
        frame_h, frame_w = frame.shape[:2]

        results = yolo_vehicle(frame, conf=0.4, verbose=False)
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls)
                if class_id not in result.names:
                    continue
                if result.names[class_id] not in ['car', 'truck', 'bus']:
                    continue

                confidence = float(box.conf)
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                grid = frame_w // 5
                pos_key = f'{cx // grid}_{cy // (frame_h // 3)}'

                # Check for plate in this frame
                car_crop = frame[y1:y2, x1:x2]
                best_plate_conf = 0
                if car_crop.size > 0:
                    try:
                        plate_results = yolo_license(car_crop, conf=0.25, verbose=False)
                        for pr in plate_results:
                            for pb in pr.boxes:
                                pc = float(pb.conf)
                                if pc > best_plate_conf:
                                    best_plate_conf = pc
                    except Exception:
                        pass

                # Score: prioritize frames where plate is visible
                new_score = (1 if best_plate_conf > 0 else 0) * 10 + best_plate_conf + confidence * 0.1
                old_score = 0
                if pos_key in unique_vehicles:
                    v = unique_vehicles[pos_key]
                    old_score = (1 if v['plate_conf'] > 0 else 0) * 10 + v['plate_conf'] + v['confidence'] * 0.1

                if new_score > old_score:
                    unique_vehicles[pos_key] = {
                        'bbox': [x1, y1, x2, y2],
                        'confidence': confidence,
                        'timestamp': timestamp,
                        'frame': frame.copy(),
                        'plate_conf': best_plate_conf,
                    }

    cap.release()
    logger.info(f'[ANALYZE] Found {len(unique_vehicles)} unique vehicles')

    # Ensure output directories
    os.makedirs('/app/car_crops', exist_ok=True)
    os.makedirs('/app/plate_crops', exist_ok=True)
    os.makedirs('/app/face_crops', exist_ok=True)

    # Process each unique vehicle
    processed = []
    idx = 0
    for pos_key, vdata in unique_vehicles.items():
        frame = vdata['frame']
        x1, y1, x2, y2 = vdata['bbox']
        car_crop = frame[y1:y2, x1:x2]
        if car_crop.size == 0:
            continue

        # Save car crop (400x300)
        crop_fn = f'car_{car.id}_v{idx}.jpg'
        crop_resized = cv2.resize(car_crop, (400, 300), interpolation=cv2.INTER_AREA)
        cv2.imwrite(f'/app/car_crops/{crop_fn}', crop_resized)

        # Detect color
        car_color = _detect_color(car_crop)

        # Detect plate
        plate_fn = None
        plate_text = None
        plate_conf = None
        best_plate_crop = None
        best_pc = 0

        plate_results = yolo_license(car_crop, conf=0.25, verbose=False)
        for pr in plate_results:
            for pb in pr.boxes:
                pc = float(pb.conf)
                px1, py1, px2, py2 = map(int, pb.xyxy[0].tolist())
                pad_x = int((px2 - px1) * 0.1)
                pad_y = int((py2 - py1) * 0.1)
                px1 = max(0, px1 - pad_x)
                py1 = max(0, py1 - pad_y)
                px2 = min(car_crop.shape[1], px2 + pad_x)
                py2 = min(car_crop.shape[0], py2 + pad_y)
                pcrop = car_crop[py1:py2, px1:px2]
                if pcrop.size > 0 and pc > best_pc:
                    best_plate_crop = pcrop
                    best_pc = pc

        if best_plate_crop is not None and best_plate_crop.size > 0:
            plate_fn = f'plate_{car.id}_v{idx}.jpg'
            plate_resized = cv2.resize(best_plate_crop, (200, 80), interpolation=cv2.INTER_CUBIC)
            cv2.imwrite(f'/app/plate_crops/{plate_fn}', plate_resized)
            plate_conf = best_pc

            # OCR with PaddleOCR (primary) + EasyOCR (fallback)
            if paddle_ocr or easyocr_reader:
                try:
                    plate_text = _read_plate_dual_ocr(best_plate_crop, paddle_ocr, easyocr_reader)
                except Exception:
                    pass

        # Driver region (right side for Saudi Arabia)
        face_fn = None
        ch, cw = car_crop.shape[:2]
        dx1, dy1 = int(cw * 0.55), int(ch * 0.10)
        dx2, dy2 = int(cw * 0.95), int(ch * 0.55)
        driver_region = car_crop[dy1:dy2, dx1:dx2]

        if driver_region.size > 0:
            face_fn = f'face_{car.id}_v{idx}.jpg'
            lab = cv2.cvtColor(driver_region, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            driver_resized = cv2.resize(enhanced, (200, 200), interpolation=cv2.INTER_AREA)
            cv2.imwrite(f'/app/face_crops/{face_fn}', driver_resized)

        processed.append({
            'vehicle_index': idx,
            'crop_image': crop_fn,
            'plate_image': plate_fn,
            'plate_text': plate_text,
            'car_color': car_color,
            'driver_face_image': face_fn,
            'vehicle_confidence': vdata['confidence'],
            'plate_confidence': plate_conf,
            'face_confidence': 1.0 if face_fn else None,
            'timestamp': vdata['timestamp'],
        })
        idx += 1

    # Save to DB - clear old detections first
    DetectedVehicle.objects.filter(video_id=car.id).delete()
    for v in processed:
        DetectedVehicle.objects.create(
            video_id=car.id,
            vehicle_index=v['vehicle_index'],
            crop_image=v['crop_image'],
            plate_image=v['plate_image'],
            plate_text=v['plate_text'],
            car_color=v['car_color'],
            driver_face_image=v['driver_face_image'],
            vehicle_confidence=v['vehicle_confidence'],
            plate_confidence=v['plate_confidence'],
            face_confidence=v['face_confidence'],
            timestamp=v['timestamp'],
        )

    summary = {
        'vehicles_detected': len(processed),
        'plates_detected': sum(1 for v in processed if v['plate_image']),
        'faces_detected': sum(1 for v in processed if v['driver_face_image']),
    }
    car.analysis = json.dumps(summary)
    car.save()

    logger.info(f'[ANALYZE] ✅ Done: {summary}')
    return summary


def _preprocess_plate_for_ocr(plate_image):
    """
    Enhanced preprocessing for KSA license plates.
    Returns (color_resized, binary_image) for dual-OCR strategy.
    """
    import cv2
    import numpy as np

    # Resize to standard width for consistent OCR
    h, w = plate_image.shape[:2]
    target_w = 400
    scale = target_w / max(w, 1)
    color_resized = cv2.resize(plate_image, (target_w, int(h * scale)), interpolation=cv2.INTER_CUBIC)

    # Grayscale
    gray = cv2.cvtColor(color_resized, cv2.COLOR_BGR2GRAY)

    # CLAHE for contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(enhanced, None, h=12, templateWindowSize=7, searchWindowSize=21)

    # Otsu's thresholding (better than adaptive for uniform plate backgrounds)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological close to fill small gaps in characters
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    return color_resized, binary


def _clean_ksa_plate(raw_text):
    """
    Clean OCR text for KSA (Saudi Arabia) license plate format.
    KSA plates: 3 Arabic letters + 4 digits  (e.g. أ ب ج 1234)
    Converts Arabic-Indic digits (٠-٩) to Western digits (0-9).
    """
    import re
    if not raw_text:
        return None

    # Remove all special characters, keep Arabic letters + digits + spaces
    text = re.sub(r'[^\u0600-\u06FF\u0660-\u0669\u06F0-\u06F90-9\s]', '', raw_text)

    # Extract Arabic letters
    arabic_letters = re.findall(r'[\u0600-\u06FF]', text)

    # Extract digits (Arabic-Indic ٠-٩ and Western 0-9)
    arabic_indic = re.findall(r'[\u0660-\u0669\u06F0-\u06F9]', text)
    western_digits = re.findall(r'[0-9]', text)

    # Convert Arabic-Indic → Western
    indic_to_western = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
    }
    converted = [indic_to_western.get(d, d) for d in arabic_indic]
    all_digits = western_digits + converted

    # Format: up to 3 Arabic letters + up to 4 digits
    letters_part = ' '.join(arabic_letters[:3]) if arabic_letters else ''
    digits_part = ''.join(all_digits[:4]) if all_digits else ''

    if letters_part and digits_part:
        return f'{letters_part} {digits_part}'
    elif digits_part:
        return digits_part
    elif letters_part:
        return letters_part
    else:
        cleaned = ' '.join(text.split())
        return cleaned if cleaned else None


def _read_plate_dual_ocr(plate_image, paddle_ocr, easyocr_reader):
    """
    Read plate text using PaddleOCR (primary) + EasyOCR (fallback).
    Tries both engines on both color and binary images.
    Returns the highest-confidence cleaned result.
    """
    import cv2
    color_img, binary_img = _preprocess_plate_for_ocr(plate_image)
    results = []

    # PaddleOCR on color image
    if paddle_ocr:
        try:
            paddle_res = paddle_ocr.ocr(color_img, cls=True)
            if paddle_res and paddle_res[0]:
                for line in paddle_res[0]:
                    text, conf = line[1][0], line[1][1]
                    cleaned = _clean_ksa_plate(text)
                    if cleaned:
                        results.append((cleaned, conf, 'paddle_color'))
        except Exception:
            pass

    # PaddleOCR on binary image
    if paddle_ocr:
        try:
            binary_3ch = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR)
            paddle_res = paddle_ocr.ocr(binary_3ch, cls=True)
            if paddle_res and paddle_res[0]:
                for line in paddle_res[0]:
                    text, conf = line[1][0], line[1][1]
                    cleaned = _clean_ksa_plate(text)
                    if cleaned:
                        results.append((cleaned, conf, 'paddle_binary'))
        except Exception:
            pass

    # EasyOCR on color image
    if easyocr_reader:
        try:
            easy_res = easyocr_reader.readtext(color_img)
            for (bbox, text, conf) in easy_res:
                cleaned = _clean_ksa_plate(text)
                if cleaned:
                    results.append((cleaned, conf, 'easy_color'))
        except Exception:
            pass

    # EasyOCR on binary image
    if easyocr_reader:
        try:
            easy_res = easyocr_reader.readtext(binary_img)
            for (bbox, text, conf) in easy_res:
                cleaned = _clean_ksa_plate(text)
                if cleaned:
                    results.append((cleaned, conf, 'easy_binary'))
        except Exception:
            pass

    if not results:
        return None

    best = max(results, key=lambda x: x[1])
    logger.info(f'[OCR] All: {[(r[0], f"{r[1]:.2f}", r[2]) for r in results]}')
    logger.info(f'[OCR] Best: "{best[0]}" (conf={best[1]:.2f}, method={best[2]})')
    return best[0]


def _detect_color(image):
    """Detect dominant car color from crop."""
    import cv2
    import numpy as np
    if image is None or image.size == 0:
        return 'Unknown'
    h, w = image.shape[:2]
    center = image[int(h * 0.3):int(h * 0.7), int(w * 0.2):int(w * 0.8)]
    if center.size == 0:
        center = image
    hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    hsv_small = cv2.resize(hsv, (30, 30))
    mh = float(np.mean(hsv_small[:, :, 0]))
    ms = float(np.mean(hsv_small[:, :, 1]))
    mv = float(np.mean(hsv_small[:, :, 2]))
    if mv > 180 and ms < 40: return 'White'
    if mv < 50: return 'Black'
    if ms < 40 and 50 <= mv <= 180: return 'Silver/Gray'
    if (mh < 10 or mh > 170) and ms > 50: return 'Red'
    if 10 <= mh < 25 and ms > 50: return 'Orange'
    if 25 <= mh < 35 and ms > 50: return 'Yellow'
    if 35 <= mh < 85 and ms > 50: return 'Green'
    if 85 <= mh < 130 and ms > 50: return 'Blue'
    if 130 <= mh < 170 and ms > 50: return 'Purple'
    return 'Unknown'


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
        return Response({'status': 'success', 'message': 'Car marked as paid'})

    @action(detail=True, methods=['post'])
    def mark_unpaid(self, request, pk=None):
        """Mark a car as unpaid."""
        car = self.get_object()
        car.paid = False
        car.save()
        return Response({'status': 'success', 'message': 'Car marked as unpaid'})

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], permission_classes=[AllowAny])
    def upload_video(self, request):
        """
        Upload a video file and automatically analyze it.
        POST /api/cars/upload_video/

        This replicates the old FastAPI flow:
        1. Save video file
        2. Create Car record
        3. Run YOLO analysis (detect vehicles, plates, faces)
        4. Save crops + DetectedVehicle records
        5. Return results

        Form data:
        - video: (file) The video file
        - plate: (string, optional) License plate number
        """
        if 'video' not in request.FILES:
            return Response({'error': 'No video file provided'}, status=status.HTTP_400_BAD_REQUEST)

        video_file = request.FILES['video']
        plate = request.data.get('plate', '').strip()

        if not plate:
            import uuid
            plate = f"UNKNOWN-{uuid.uuid4().hex[:8].upper()}"

        # Validate file size (max 500MB)
        if video_file.size > 500 * 1024 * 1024:
            return Response({'error': 'Video file too large. Max size: 500MB'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file type
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        file_ext = os.path.splitext(video_file.name)[1].lower()
        if file_ext not in allowed_extensions:
            return Response({'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Step 1: Save video
            video_filename = video_file.name
            video_dir = '/app/videos'
            os.makedirs(video_dir, exist_ok=True)
            video_path = os.path.join(video_dir, video_filename)

            with open(video_path, 'wb+') as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)

            # Step 2: Create Car record
            car = Car.objects.create(plate=plate, video=video_filename, paid=False)
            logger.info(f'[UPLOAD] Video saved: {video_filename}, Car ID: {car.id}')

            # Step 3: Check if this plate was seen before and unpaid
            existing_unpaid = Car.objects.filter(plate=plate, paid=False).exclude(id=car.id).first()
            alert = None
            if existing_unpaid:
                alert = {
                    'type': 'unpaid_return',
                    'message': f'⚠️ This plate ({plate}) has a previous UNPAID visit!',
                    'previous_car_id': existing_unpaid.id,
                }

            # Step 4: Start analysis in background (non-blocking)
            import subprocess
            log_file = open('/app/analysis.log', 'a')
            subprocess.Popen(
                ['python', 'manage.py', 'analyze_video', str(car.id)],
                cwd='/app',
                stdout=log_file,
                stderr=log_file,
            )
            logger.info(f'[UPLOAD] Background analysis started for car_id={car.id}')

            response_data = {
                'success': True,
                'car_id': car.id,
                'message': 'Video uploaded. Analysis started in background.',
                'video_name': video_filename,
                'plate': plate,
            }
            if alert:
                response_data['alert'] = alert

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': f'Upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def analyze(self, request, pk=None):
        """
        Manually trigger analysis for a specific car.
        POST /api/cars/{id}/analyze/
        """
        car = self.get_object()
        if not car.video:
            return Response({'error': 'Car has no video'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = analyze_video_for_car(car)
            return Response({'success': True, 'analysis': result})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def check_plate(self, request):
        """
        Check if a plate has unpaid visits.
        GET /api/cars/check_plate/?plate=ABC-123
        Returns alert if plate has unpaid history.
        """
        plate = request.query_params.get('plate', '').strip()
        if not plate:
            return Response({'error': 'plate parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        unpaid_cars = Car.objects.filter(plate=plate, paid=False)
        if unpaid_cars.exists():
            return Response({
                'alert': True,
                'plate': plate,
                'unpaid_count': unpaid_cars.count(),
                'message': f'⚠️ Plate {plate} has {unpaid_cars.count()} unpaid visit(s)!',
            })
        return Response({'alert': False, 'plate': plate, 'message': 'No unpaid visits'})

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def analysis_status(self, request):
        """
        Check analysis status for a car.
        GET /api/cars/analysis_status/?car_id=10
        """
        car_id = request.query_params.get('car_id')
        if not car_id:
            return Response({'error': 'car_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            car = Car.objects.get(id=car_id)
            vehicle_count = DetectedVehicle.objects.filter(video_id=car.id).count()
            return Response({
                'car_id': car.id,
                'analyzed': vehicle_count > 0,
                'vehicle_count': vehicle_count,
                'analysis': car.analysis,
            })
        except Car.DoesNotExist:
            return Response({'error': 'Car not found'}, status=status.HTTP_404_NOT_FOUND)
