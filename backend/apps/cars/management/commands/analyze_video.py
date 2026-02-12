"""
Django management command to analyze videos and detect vehicles, plates, faces.
Runs YOLO + PaddleOCR (primary) + EasyOCR (fallback) inside Docker.

Usage: python manage.py analyze_video <car_id>
       python manage.py analyze_video --all
"""
import os
import re
import json
import cv2
import numpy as np
from django.core.management.base import BaseCommand
from apps.cars.models import Car
from apps.vehicles.models import DetectedVehicle


class Command(BaseCommand):
    help = 'Analyze a video using YOLO to detect vehicles, plates, and faces'

    def add_arguments(self, parser):
        parser.add_argument('car_id', nargs='?', type=int, help='Car ID to analyze')
        parser.add_argument('--all', action='store_true', help='Analyze all unanalyzed videos')

    def handle(self, *args, **options):
        from ultralytics import YOLO

        self.stdout.write('Loading YOLO models...')
        self.yolo_vehicle = YOLO('/app/yolov8n.pt')
        self.yolo_license = YOLO('/app/best.pt')
        self.stdout.write(self.style.SUCCESS('✅ Models loaded'))

        # Primary OCR: PaddleOCR (better Arabic accuracy for KSA plates)
        self.paddle_ocr = None
        try:
            from paddleocr import PaddleOCR
            self.paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang='ar',
                show_log=False,
                use_gpu=False,
            )
            self.stdout.write(self.style.SUCCESS('✅ PaddleOCR loaded (primary OCR)'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ PaddleOCR not available: {e}'))

        # Fallback OCR: EasyOCR
        self.easyocr_reader = None
        try:
            import easyocr
            self.easyocr_reader = easyocr.Reader(['en', 'ar'], gpu=False)
            self.stdout.write(self.style.SUCCESS('✅ EasyOCR loaded (fallback OCR)'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ EasyOCR not available: {e}'))

        if options.get('all'):
            cars = Car.objects.filter(video__isnull=False).exclude(video='')
            for car in cars:
                self.analyze_car(car)
        elif options.get('car_id'):
            try:
                car = Car.objects.get(id=options['car_id'])
                self.analyze_car(car)
            except Car.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Car {options["car_id"]} not found'))
        else:
            self.stdout.write(self.style.ERROR('Provide a car_id or use --all'))

    def analyze_car(self, car):
        video_path = f'/app/videos/{car.video}'
        if not os.path.exists(video_path):
            self.stdout.write(self.style.ERROR(f'Video not found: {video_path}'))
            return

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'Analyzing Car ID={car.id}, Plate={car.plate}, Video={car.video}')
        self.stdout.write(f'{"="*60}')

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.stdout.write(self.style.ERROR('Failed to open video'))
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.stdout.write(f'Video: {frame_count} frames, {fps:.1f} FPS')

        frame_interval = max(1, int(fps))
        frame_indices = list(range(0, frame_count, frame_interval))

        unique_vehicles = {}

        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue

            timestamp = frame_idx / fps if fps > 0 else 0
            frame_h, frame_w = frame.shape[:2]

            results = self.yolo_vehicle(frame, conf=0.4, verbose=False)
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls)
                    if class_id not in result.names:
                        continue
                    class_name = result.names[class_id]
                    if class_name not in ['car', 'truck', 'bus']:
                        continue

                    confidence = float(box.conf)
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    grid = frame_w // 5
                    pos_key = f'{cx // grid}_{cy // (frame_h // 3)}'

                    car_crop = frame[y1:y2, x1:x2]
                    best_plate_conf = 0
                    if car_crop.size > 0:
                        try:
                            plate_results = self.yolo_license(car_crop, conf=0.25, verbose=False)
                            for pr in plate_results:
                                for pb in pr.boxes:
                                    pc = float(pb.conf)
                                    if pc > best_plate_conf:
                                        best_plate_conf = pc
                        except:
                            pass

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
        self.stdout.write(f'Found {len(unique_vehicles)} unique vehicles')

        os.makedirs('/app/car_crops', exist_ok=True)
        os.makedirs('/app/plate_crops', exist_ok=True)
        os.makedirs('/app/face_crops', exist_ok=True)

        processed = []
        idx = 0
        for pos_key, vdata in unique_vehicles.items():
            frame = vdata['frame']
            x1, y1, x2, y2 = vdata['bbox']
            car_crop = frame[y1:y2, x1:x2]
            if car_crop.size == 0:
                continue

            crop_resized = cv2.resize(car_crop, (400, 300), interpolation=cv2.INTER_AREA)
            crop_fn = f'car_{car.id}_v{idx}.jpg'
            cv2.imwrite(f'/app/car_crops/{crop_fn}', crop_resized)
            self.stdout.write(f'  [CAR] Saved {crop_fn}')

            car_color = self.detect_color(car_crop)

            plate_fn = None
            plate_text = None
            plate_conf = None
            best_plate_crop = None
            best_pc = 0

            plate_results = self.yolo_license(car_crop, conf=0.25, verbose=False)
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
                self.stdout.write(f'  [PLATE] Saved {plate_fn} (conf: {best_pc:.2f})')
                plate_text = self.ocr_plate(best_plate_crop)
                if plate_text:
                    self.stdout.write(f'  [OCR] Plate text: {plate_text}')

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
                self.stdout.write(f'  [DRIVER] Saved {face_fn}')

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

        self.stdout.write(self.style.SUCCESS(
            f'✅ Done! {summary["vehicles_detected"]} vehicles, '
            f'{summary["plates_detected"]} plates, '
            f'{summary["faces_detected"]} driver images'
        ))

    def detect_color(self, image):
        if image is None or image.size == 0:
            return 'Unknown'
        h, w = image.shape[:2]
        center = image[int(h*0.3):int(h*0.7), int(w*0.2):int(w*0.8)]
        if center.size == 0:
            center = image
        hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
        hsv_small = cv2.resize(hsv, (30, 30))
        mh = np.mean(hsv_small[:, :, 0])
        ms = np.mean(hsv_small[:, :, 1])
        mv = np.mean(hsv_small[:, :, 2])
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

    def ocr_plate(self, plate_image):
        """
        Read plate text using PaddleOCR (primary) + EasyOCR (fallback).
        Picks the highest-confidence result. Cleans output for KSA plate format.
        """
        if plate_image is None:
            return None
        try:
            color_img, binary_img = self.preprocess_plate(plate_image)
            results = []

            # --- Method 1: PaddleOCR on color image (best for Arabic) ---
            if self.paddle_ocr:
                try:
                    paddle_res = self.paddle_ocr.ocr(color_img, cls=True)
                    if paddle_res and paddle_res[0]:
                        for line in paddle_res[0]:
                            text, conf = line[1][0], line[1][1]
                            cleaned = self.clean_ksa_plate(text)
                            if cleaned:
                                results.append((cleaned, conf, 'paddle_color'))
                except Exception as e:
                    self.stdout.write(f'  [OCR] PaddleOCR color error: {e}')

            # --- Method 2: PaddleOCR on binary image ---
            if self.paddle_ocr:
                try:
                    binary_3ch = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR)
                    paddle_res = self.paddle_ocr.ocr(binary_3ch, cls=True)
                    if paddle_res and paddle_res[0]:
                        for line in paddle_res[0]:
                            text, conf = line[1][0], line[1][1]
                            cleaned = self.clean_ksa_plate(text)
                            if cleaned:
                                results.append((cleaned, conf, 'paddle_binary'))
                except Exception as e:
                    self.stdout.write(f'  [OCR] PaddleOCR binary error: {e}')

            # --- Method 3: EasyOCR on color image (fallback) ---
            if self.easyocr_reader:
                try:
                    easy_res = self.easyocr_reader.readtext(color_img)
                    for (bbox, text, conf) in easy_res:
                        cleaned = self.clean_ksa_plate(text)
                        if cleaned:
                            results.append((cleaned, conf, 'easy_color'))
                except Exception as e:
                    self.stdout.write(f'  [OCR] EasyOCR color error: {e}')

            # --- Method 4: EasyOCR on binary image (last resort) ---
            if self.easyocr_reader:
                try:
                    easy_res = self.easyocr_reader.readtext(binary_img)
                    for (bbox, text, conf) in easy_res:
                        cleaned = self.clean_ksa_plate(text)
                        if cleaned:
                            results.append((cleaned, conf, 'easy_binary'))
                except Exception as e:
                    self.stdout.write(f'  [OCR] EasyOCR binary error: {e}')

            if not results:
                return None

            # Pick highest confidence
            best = max(results, key=lambda x: x[1])
            self.stdout.write(f'  [OCR] All: {[(r[0], f"{r[1]:.2f}", r[2]) for r in results]}')
            self.stdout.write(f'  [OCR] Best: "{best[0]}" (conf={best[1]:.2f}, method={best[2]})')
            return best[0]

        except Exception as e:
            self.stdout.write(f'  [OCR] Error: {e}')
        return None

    def clean_ksa_plate(self, raw_text):
        """
        Clean OCR text for KSA (Saudi Arabia) license plate format.
        KSA plates: 3 Arabic letters + 4 digits  (e.g. أ ب ج 1234)
        Converts Arabic-Indic digits (٠-٩) to Western digits (0-9).
        """
        if not raw_text:
            return None

        # Remove all special characters, keep Arabic letters + digits + spaces
        text = re.sub(r'[^\u0600-\u06FF\u0660-\u0669\u06F0-\u06F90-9\s]', '', raw_text)

        # Extract Arabic letters
        arabic_letters = re.findall(r'[\u0600-\u06FF]', text)

        # Extract digits (Arabic-Indic ٠-٩ and Western 0-9)
        arabic_indic = re.findall(r'[\u0660-\u0669\u06F0-\u06F9]', text)
        western_digits = re.findall(r'[0-9]', text)

        # Convert Arabic-Indic digits → Western
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

    def preprocess_plate(self, plate_image):
        """
        Enhanced preprocessing for KSA plates.
        Returns (color_resized, binary_image) for dual-OCR strategy.
        """
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
