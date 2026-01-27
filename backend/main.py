from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
import json
import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import io
from fastapi.responses import StreamingResponse

# Try to import EasyOCR
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    print("[OCR] EasyOCR library available")
except ImportError:
    EASYOCR_AVAILABLE = False
    print("[OCR] EasyOCR not installed")
    easyocr = None

# Set CPU optimization
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['OPENBLAS_NUM_THREADS'] = '4'

# Initialize EasyOCR reader for Arabic and English (Saudi plates)
easyocr_reader = None
OCR_AVAILABLE = False
OCR_TYPE = None

print("[OCR] Initializing EasyOCR for Arabic and English...")
if EASYOCR_AVAILABLE:
    try:
        # Initialize with both English and Arabic for Saudi license plates
        easyocr_reader = easyocr.Reader(['en', 'ar'], gpu=False, model_storage_directory=os.path.expanduser('~/.EasyOCR'))
        print("[OCR] ✅ EasyOCR initialized successfully")
        OCR_AVAILABLE = True
        OCR_TYPE = 'easyocr'
    except Exception as e:
        print(f"[OCR] ❌ EasyOCR initialization error: {e}")
        easyocr_reader = None
        OCR_AVAILABLE = False
else:
    print("[OCR] ⚠️  EasyOCR not available - OCR features will be disabled")

# --- DATABASE SETUP ---
# Get PostgreSQL connection string from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin123@localhost:5432/gas_station")

print(f"[DB] Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Test connections before using
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()

# --- DATABASE MODELS ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="employee")

class Car(Base):
    __tablename__ = "cars"
    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String, nullable=False)
    detected_plate = Column(String, nullable=True)
    paid = Column(Integer, default=1)  # Default to PAID (1), user marks as unpaid if needed
    video = Column(String, nullable=True)
    analysis = Column(Text, nullable=True)

class DetectedVehicle(Base):
    __tablename__ = "detected_vehicles"
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("cars.id"), nullable=False)
    vehicle_index = Column(Integer, nullable=False)
    crop_image = Column(String, nullable=True)
    plate_image = Column(String, nullable=True)
    plate_text = Column(String, nullable=True)
    car_color = Column(String, nullable=True)
    driver_face_image = Column(String, nullable=True)
    vehicle_confidence = Column(Float, nullable=True)
    plate_confidence = Column(Float, nullable=True)
    face_confidence = Column(Float, nullable=True)
    timestamp = Column(Float, nullable=True)

# Create all tables
try:
    Base.metadata.create_all(bind=engine)
    print("[DB] ✅ Database tables created successfully")
except Exception as e:
    print(f"[DB] ⚠️  Error creating tables: {e}")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTH ---
@app.post("/register")
def register(username: str = Form(...), password: str = Form(...), role: str = Form("employee"), db: Session = Depends(get_db)):
    # Check if user exists
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new user
    new_user = User(username=username, password=password, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"status": "registered", "username": username, "role": role}

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Demo users
    if username == "admin" and password == "admin":
        return {"role": "admin", "name": "Administrator"}
    elif username == "employee" and password == "employee":
        return {"role": "employee", "name": "Employee User"}
    
    # Check database for user
    user = db.query(User).filter(User.username == username, User.password == password).first()
    if user:
        return {"role": user.role, "name": username}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

# --- CARS ---
@app.get("/cars")
def get_all_cars(db: Session = Depends(get_db)):
    cars = db.query(Car).all()
    result = []
    for car in cars:
        car_dict = {
            "id": car.id,
            "plate": car.plate,
            "detected_plate": car.detected_plate,
            "paid": car.paid,
            "video": car.video,
            "analysis": json.loads(car.analysis) if car.analysis else None
        }
        result.append(car_dict)
    return result

@app.get("/cars/{car_id}")
def get_car(car_id: int, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return {
        "id": car.id,
        "plate": car.plate,
        "detected_plate": car.detected_plate,
        "paid": car.paid,
        "video": car.video,
        "analysis": json.loads(car.analysis) if car.analysis else None
    }

@app.get("/cars-with-analysis")
def get_cars_with_analysis(db: Session = Depends(get_db)):
    """Get all cars with their video data (analysis optional) and first vehicle's details"""
    cars = db.query(Car).all()
    result = []
    for car in cars:
        car_dict = {
            "id": car.id,
            "plate": car.plate,
            "detected_plate": car.detected_plate,
            "paid": car.paid,
            "video": car.video,
            "analysis": json.loads(car.analysis) if car.analysis else None
        }
        
        # Get the first detected vehicle for this car's video to include image/color data
        first_vehicle = db.query(DetectedVehicle).filter(
            DetectedVehicle.video_id == car.id
        ).order_by(DetectedVehicle.vehicle_index).first()
        
        if first_vehicle:
            car_dict["crop_image"] = first_vehicle.crop_image
            car_dict["plate_image"] = first_vehicle.plate_image
            car_dict["car_color"] = first_vehicle.car_color
            car_dict["driver_face_image"] = first_vehicle.driver_face_image
        
        result.append(car_dict)
    return result

@app.get("/detected-vehicles")
def get_detected_vehicles(db: Session = Depends(get_db)):
    """Get all detected individual vehicles (cropped images)"""
    vehicles = db.query(DetectedVehicle).all()
    result = []
    for v in vehicles:
        result.append({
            "id": v.id,
            "video_id": v.video_id,
            "vehicle_index": v.vehicle_index,
            "crop_image": v.crop_image,
            "plate_image": v.plate_image,
            "plate_text": v.plate_text,
            "car_color": v.car_color,
            "driver_face_image": v.driver_face_image,
            "vehicle_confidence": v.vehicle_confidence,
            "plate_confidence": v.plate_confidence,
            "face_confidence": v.face_confidence,
            "timestamp": v.timestamp
        })
    return result

@app.put("/detected-vehicles/{vehicle_id}/plate")
def update_vehicle_plate(vehicle_id: int, data: dict, db: Session = Depends(get_db)):
    """Update the plate text for a detected vehicle"""
    vehicle = db.query(DetectedVehicle).filter(DetectedVehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    vehicle.plate_text = data.get("plate_text", "")
    db.commit()
    return {"status": "ok", "plate_text": vehicle.plate_text}

@app.get("/detected-vehicles/{video_id}")
def get_detected_vehicles_for_video(video_id: int, db: Session = Depends(get_db)):
    """Get all detected vehicles from a specific video"""
    vehicles = db.query(DetectedVehicle).filter(DetectedVehicle.video_id == video_id).order_by(DetectedVehicle.vehicle_index).all()
    result = []
    for v in vehicles:
        result.append({
            "id": v.id,
            "video_id": v.video_id,
            "vehicle_index": v.vehicle_index,
            "crop_image": v.crop_image,
            "plate_image": v.plate_image,
            "plate_text": v.plate_text,
            "car_color": v.car_color,
            "driver_face_image": v.driver_face_image,
            "vehicle_confidence": v.vehicle_confidence,
            "plate_confidence": v.plate_confidence,
            "face_confidence": v.face_confidence,
            "timestamp": v.timestamp
        })
    return result

@app.get("/cars/unpaid")
def get_unpaid_cars(db: Session = Depends(get_db)):
    cars = db.query(Car).filter(Car.paid == 0).all()
    result = []
    for car in cars:
        car_dict = {
            "id": car.id,
            "plate": car.plate,
            "detected_plate": car.detected_plate,
            "paid": car.paid,
            "video": car.video,
            "analysis": json.loads(car.analysis) if car.analysis else None
        }
        result.append(car_dict)
    return result

@app.get("/car-video-frame/{car_id}")
def get_car_video_frame(car_id: int, db: Session = Depends(get_db)):
    """Extract first frame from car video as JPEG"""
    from fastapi.responses import StreamingResponse
    import io
    
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car or not car.video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_path = car.video
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    try:
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise HTTPException(status_code=500, detail="Could not read video frame")
        
        # Resize frame
        frame = cv2.resize(frame, (400, 300))
        
        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        
        return StreamingResponse(io.BytesIO(buffer.tobytes()), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cars/pay/{car_id}")
def mark_car_paid(car_id: int, db: Session = Depends(get_db)):
    print(f"[PAY] Attempting to toggle payment for car {car_id}")
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        print(f"[PAY] Car {car_id} not found in database. Creating it with paid=1")
        car = Car(id=car_id, plate=f"Auto-{car_id}", paid=1)
        db.add(car)
        db.commit()
        db.refresh(car)
        return {"status": "created_and_paid", "car_id": car_id, "paid": 1}
    
    old_paid = car.paid
    # Toggle: if paid (1), mark as unpaid (0), if unpaid (0), mark as paid (1)
    car.paid = 1 - car.paid
    db.commit()
    print(f"[PAY] Car {car_id} payment toggled: {old_paid} → {car.paid}")
    return {"status": "toggled", "car_id": car_id, "paid": car.paid, "was_paid": bool(old_paid)}

@app.post("/cars")
def add_car(plate: str = Form(...), db: Session = Depends(get_db)):
    new_car = Car(plate=plate, paid=0)
    db.add(new_car)
    db.commit()
    db.refresh(new_car)
    return {"id": new_car.id, "plate": plate, "paid": 0}

# --- VIDEO UPLOAD ---
os.makedirs("videos", exist_ok=True)
os.makedirs("car_crops", exist_ok=True)  # Directory for cropped car images
os.makedirs("plate_crops", exist_ok=True)  # Directory for license plate crops
os.makedirs("face_crops", exist_ok=True)  # Directory for driver face crops
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/car_crops", StaticFiles(directory="car_crops"), name="car_crops")
app.mount("/plate_crops", StaticFiles(directory="plate_crops"), name="plate_crops")
app.mount("/face_crops", StaticFiles(directory="face_crops"), name="face_crops")

# Load YOLO models
yolo_vehicle = YOLO("yolov8n.pt")  # Default model for person/car detection
yolo_license = YOLO("best.pt")  # Your trained model for license plate detection

# Try to load face detection model
try:
    yolo_face = YOLO("yolov8n-face.pt")  # Face detection model
    FACE_MODEL_AVAILABLE = True
except:
    yolo_face = yolo_vehicle  # Fallback to person detection
    FACE_MODEL_AVAILABLE = False

def detect_car_color(image):
    """Detect dominant color of a car from its cropped image"""
    if image is None or image.size == 0:
        return "Unknown"
    
    # Focus on the center of the car (avoid windows, wheels, background)
    h, w = image.shape[:2]
    # Take the middle portion of the car
    center_y1, center_y2 = int(h * 0.3), int(h * 0.7)
    center_x1, center_x2 = int(w * 0.2), int(w * 0.8)
    center_crop = image[center_y1:center_y2, center_x1:center_x2]
    
    if center_crop.size == 0:
        center_crop = image
    
    # Convert to HSV for better color detection
    img_hsv = cv2.cvtColor(center_crop, cv2.COLOR_BGR2HSV)
    img_rgb = cv2.cvtColor(center_crop, cv2.COLOR_BGR2RGB)
    
    # Resize for faster processing
    img_hsv_small = cv2.resize(img_hsv, (30, 30))
    img_rgb_small = cv2.resize(img_rgb, (30, 30))
    
    # Get mean HSV values
    mean_h = np.mean(img_hsv_small[:, :, 0])
    mean_s = np.mean(img_hsv_small[:, :, 1])
    mean_v = np.mean(img_hsv_small[:, :, 2])
    
    # Get mean RGB values
    mean_r = np.mean(img_rgb_small[:, :, 0])
    mean_g = np.mean(img_rgb_small[:, :, 1])
    mean_b = np.mean(img_rgb_small[:, :, 2])
    
    # Color classification using HSV
    # White: high value, low saturation
    if mean_v > 180 and mean_s < 40:
        return "White"
    
    # Black: low value
    if mean_v < 50:
        return "Black"
    
    # Silver/Gray: medium value, low saturation
    if mean_s < 40 and 50 <= mean_v <= 180:
        return "Silver/Gray"
    
    # For chromatic colors, use hue
    # Red: hue 0-10 or 170-180
    if (mean_h < 10 or mean_h > 170) and mean_s > 50:
        return "Red"
    
    # Orange: hue 10-25
    if 10 <= mean_h < 25 and mean_s > 50:
        return "Orange"
    
    # Yellow: hue 25-35
    if 25 <= mean_h < 35 and mean_s > 50:
        return "Yellow"
    
    # Green: hue 35-85
    if 35 <= mean_h < 85 and mean_s > 50:
        return "Green"
    
    # Blue: hue 85-130
    if 85 <= mean_h < 130 and mean_s > 50:
        return "Blue"
    
    # Purple: hue 130-170
    if 130 <= mean_h < 170 and mean_s > 50:
        return "Purple"
    
    # Beige/Tan: low saturation with warm tones
    if mean_s < 60 and mean_r > mean_b and mean_v > 100:
        return "Beige"
    
    # Brown: darker warm tones
    if mean_r > mean_b and mean_v < 150 and mean_s > 30:
        return "Brown"
    
    return "Unknown"

def deskew_plate(image):
    """Correct skewed/rotated license plates for better OCR"""
    try:
        if image is None or image.size == 0:
            return image
        
        # Find contours
        coords = np.column_stack(np.where(image > 0))
        if len(coords) < 4:
            return image
        
        # Get angle from minimum area rectangle
        angle = cv2.minAreaRect(coords)[-1]
        
        # Adjust angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        # Skip if angle is too small (not worth rotating)
        if abs(angle) < 2:
            return image
        
        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), 
                                flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)
        
        return rotated
    except Exception as e:
        print(f"[DESKEW] Error: {e}")
        return image

def remove_border_noise(image):
    """Remove border artifacts from images"""
    if image is None or image.size == 0:
        return image
    
    h, w = image.shape[:2]
    # Remove 2 pixels from each border
    if h > 4 and w > 4:
        return image[2:h-2, 2:w-2]
    return image

def preprocess_plate_image(plate_image):
    """
    Enhanced image preprocessing pipeline for license plate OCR
    
    Steps:
    1. Resize - Scale to standard size (minimum 200px width)
    2. Denoise - Remove camera grain/noise
    3. Deskew - Correct rotated plates
    4. CLAHE - Increase contrast adaptively
    5. Sharpen - Make characters clearer
    6. Threshold - Convert to binary (black text on white)
    7. Morphology - Clean artifacts
    
    Returns dict with multiple processed versions for OCR to try
    """
    if plate_image is None or plate_image.size == 0:
        return None
    
    try:
        print(f"[PREPROCESS] Starting with image shape: {plate_image.shape}")
        
        # Step 1: Resize to standard size for better OCR
        height, width = plate_image.shape[:2]
        if width < 200:  # If too small, upscale
            scale = max(1.5, 200 / width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized = cv2.resize(plate_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            print(f"[PREPROCESS] Upscaled {(height, width)} → {(new_height, new_width)}")
        else:
            resized = plate_image
        
        # Convert to grayscale
        if len(resized.shape) == 3:
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        else:
            gray = resized
        
        print(f"[PREPROCESS] Converted to grayscale, shape: {gray.shape}")
        
        # Step 2: Denoise (remove camera grain/noise)
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
        print("[PREPROCESS] Applied denoising")
        
        # Step 3: Deskew if needed (correct rotated plates)
        deskewed = deskew_plate(denoised)
        print("[PREPROCESS] Applied deskewing")
        
        # Step 4: Increase contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(deskewed)
        print("[PREPROCESS] Applied CLAHE contrast enhancement")
        
        # Step 5: Sharpen the image
        sharpen_kernel = np.array([[-1, -1, -1],
                                   [-1,  9, -1],
                                   [-1, -1, -1]], dtype=np.float32)
        sharpened = cv2.filter2D(contrast_enhanced, -1, sharpen_kernel)
        print("[PREPROCESS] Applied sharpening")
        
        # Step 6: Binary thresholding - try multiple methods
        # Method 1: Otsu's thresholding (automatic threshold selection)
        _, otsu_thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        print("[PREPROCESS] Applied Otsu thresholding")
        
        # Method 2: Adaptive thresholding (better for varying lighting)
        adaptive_thresh = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3
        )
        print("[PREPROCESS] Applied adaptive thresholding")
        
        # Method 3: Inverse threshold (for white text on dark background)
        _, otsu_inv = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        adaptive_inv = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 3
        )
        print("[PREPROCESS] Applied inverse thresholding")
        
        # Step 7: Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        otsu_morph = cv2.morphologyEx(otsu_thresh, cv2.MORPH_CLOSE, kernel)
        adaptive_morph = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
        print("[PREPROCESS] Applied morphological operations")
        
        # Step 8: Remove border noise
        otsu_cleaned = remove_border_noise(otsu_morph)
        adaptive_cleaned = remove_border_noise(adaptive_morph)
        print("[PREPROCESS] Removed border noise")
        
        print("[PREPROCESS] ✅ All preprocessing steps completed successfully")
        
        return {
            'gray': gray,
            'denoised': denoised,
            'deskewed': deskewed,
            'contrast': contrast_enhanced,
            'sharpened': sharpened,
            'otsu': otsu_thresh,
            'otsu_morph': otsu_cleaned,
            'adaptive': adaptive_thresh,
            'adaptive_morph': adaptive_cleaned,
            'otsu_inv': otsu_inv,
            'adaptive_inv': adaptive_inv,
        }
    except Exception as e:
        print(f"[PREPROCESS] ❌ Preprocessing error: {e}")
        import traceback
        traceback.print_exc()
        return None

def read_license_plate_text(plate_image):
    """Use OCR to read license plate text with enhanced preprocessing
    
    Tries both English and Arabic OCR readers for Saudi plates
    Uses aggressive image enhancement for better results
    """
    if not OCR_AVAILABLE or plate_image is None or plate_image.size == 0:
        return None
    
    try:
        print(f"[OCR] Starting OCR for image shape {plate_image.shape}")
        
        # Step 1: Aggressive image enhancement for license plates
        enhanced_images = []
        
        # Original color image
        enhanced_images.append(("original", plate_image))
        
        # Convert to grayscale
        if len(plate_image.shape) == 3:
            gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_image.copy()
        
        # Resize if too small (minimum 300px width for better OCR)
        h, w = gray.shape[:2]
        if w < 300:
            scale = 300 / w
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            print(f"[OCR] Upscaled image to {gray.shape}")
        
        enhanced_images.append(("gray", gray))
        
        # Strong CLAHE contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(gray)
        enhanced_images.append(("clahe", clahe_img))
        
        # Bilateral filter (edge-preserving smoothing)
        bilateral = cv2.bilateralFilter(gray, 11, 17, 17)
        enhanced_images.append(("bilateral", bilateral))
        
        # Gaussian blur + sharpen
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(blur, -1, sharpen_kernel)
        enhanced_images.append(("sharpened", sharpened))
        
        # Otsu thresholding
        _, otsu = cv2.threshold(clahe_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        enhanced_images.append(("otsu", otsu))
        
        # Inverse Otsu (for white text on dark)
        _, otsu_inv = cv2.threshold(clahe_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        enhanced_images.append(("otsu_inv", otsu_inv))
        
        # Adaptive threshold
        adaptive = cv2.adaptiveThreshold(clahe_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        enhanced_images.append(("adaptive", adaptive))
        
        # Morphological closing to connect broken characters
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph_close = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
        enhanced_images.append(("morph", morph_close))
        
        all_results = []
        
        # Try BOTH English and Arabic OCR on each image
        for img_name, img in enhanced_images:
            # Try English OCR
            if ocr_reader_en:
                try:
                    results = ocr_reader_en.ocr(img, cls=True)
                    if results and results[0]:
                        for line in results[0]:
                            if line and len(line) >= 2:
                                text = line[1][0] if isinstance(line[1], tuple) else line[1]
                                conf = line[1][1] if isinstance(line[1], tuple) else 0.5
                                if isinstance(text, str) and len(text) >= 1 and conf > 0.1:
                                    all_results.append({
                                        'text': text,
                                        'confidence': conf,
                                        'source': f'{img_name}_en',
                                        'lang': 'en'
                                    })
                                    print(f"[OCR-EN] {img_name}: '{text}' (conf: {conf:.2f})")
                except Exception as e:
                    print(f"[OCR-EN] Error on {img_name}: {e}")
            
            # Try Arabic OCR (for Saudi plates)
            if ocr_reader_ar:
                try:
                    results = ocr_reader_ar.ocr(img, cls=True)
                    if results and results[0]:
                        for line in results[0]:
                            if line and len(line) >= 2:
                                text = line[1][0] if isinstance(line[1], tuple) else line[1]
                                conf = line[1][1] if isinstance(line[1], tuple) else 0.5
                                if isinstance(text, str) and len(text) >= 1 and conf > 0.1:
                                    all_results.append({
                                        'text': text,
                                        'confidence': conf,
                                        'source': f'{img_name}_ar',
                                        'lang': 'ar'
                                    })
                                    print(f"[OCR-AR] {img_name}: '{text}' (conf: {conf:.2f})")
                except Exception as e:
                    print(f"[OCR-AR] Error on {img_name}: {e}")
        
        print(f"[OCR] Total results collected: {len(all_results)}")
        
        if all_results:
            # Sort by confidence
            all_results.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Show top results
            print(f"[OCR] Top 5 results:")
            for i, r in enumerate(all_results[:5]):
                print(f"  {i+1}. '{r['text']}' (conf: {r['confidence']:.2f}, src: {r['source']})")
            
            # Combine all text segments with confidence > 0.3
            valid_results = [r for r in all_results if r['confidence'] > 0.3]
            
            if valid_results:
                # Collect unique text segments
                seen = set()
                final_parts = []
                for r in valid_results:
                    # Clean the text - keep alphanumeric, Arabic chars, and spaces
                    cleaned = ''.join(c for c in r['text'] if c.isalnum() or c.isspace() or '\u0600' <= c <= '\u06FF')
                    cleaned = cleaned.strip()
                    if cleaned and cleaned.lower() not in seen and len(cleaned) >= 1:
                        seen.add(cleaned.lower())
                        final_parts.append(cleaned)
                
                if final_parts:
                    # Combine up to 3 parts
                    final_text = ' '.join(final_parts[:3]).strip().upper()
                    print(f"[OCR] ✅ Final result (PaddleOCR): {final_text}")
                    return final_text
            
            # Fallback to best single result
            best = all_results[0]
            if best['confidence'] > 0.15:
                final_text = best['text'].strip().upper()
                print(f"[OCR] ✅ Final result (PaddleOCR fallback): {final_text}")
                return final_text
        
        # If PaddleOCR fails or finds nothing, try EasyOCR
        if EASYOCR_AVAILABLE and easyocr_reader:
            print("[OCR] PaddleOCR found nothing, trying EasyOCR as fallback...")
            try:
                # EasyOCR detection
                results = easyocr_reader.readtext(plate_image, detail=1)
                if results:
                    easy_results = []
                    for detection in results:
                        if len(detection) >= 2:
                            text = detection[1]
                            conf = detection[2]
                            if isinstance(text, str) and len(text) >= 1 and conf > 0.1:
                                easy_results.append({'text': text, 'confidence': conf})
                                print(f"[OCR-Easy] '{text}' (conf: {conf:.2f})")
                    
                    if easy_results:
                        # Sort by confidence
                        easy_results.sort(key=lambda x: x['confidence'], reverse=True)
                        final_text = ' '.join([r['text'] for r in easy_results[:3]]).strip().upper()
                        print(f"[OCR] ✅ Final result (EasyOCR): {final_text}")
                        return final_text
            except Exception as e:
                print(f"[OCR] EasyOCR error: {e}")
        
        print("[OCR] ❌ No valid results found from any OCR engine")
        return None
        
    except Exception as e:
        print(f"[OCR] ❌ OCR Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def bbox_overlap(bbox1, bbox2, threshold=0.5):
    """Check if two bounding boxes overlap (person inside car)"""
    x1_min, y1_min, x1_max, y1_max = bbox1
    x2_min, y2_min, x2_max, y2_max = bbox2
    
    # Calculate intersection
    inter_xmin = max(x1_min, x2_min)
    inter_ymin = max(y1_min, y2_min)
    inter_xmax = min(x1_max, x2_max)
    inter_ymax = min(y1_max, y2_max)
    
    if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
        return False
    
    # Calculate intersection area
    inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
    
    # Calculate person bbox area
    person_area = (x1_max - x1_min) * (y1_max - y1_min)
    
    # Check if person is mostly inside car
    overlap_ratio = inter_area / person_area
    return overlap_ratio > threshold

@app.post("/upload-car-video/{car_id}")
async def upload_car_video(car_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = f"videos/{car_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Check if car exists, if not create it
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        car = Car(id=car_id, plate=f"Car {car_id}", video=file_path)
        db.add(car)
    else:
        car.video = file_path
    db.commit()
    
    # Automatically analyze the video after upload
    print(f"[AUTO-ANALYZE] Starting analysis for car_id={car_id}")
    try:
        analysis_result = await analyze_video(car_id, db)
        print(f"[AUTO-ANALYZE] Completed for car_id={car_id}")
        return {"filename": file.filename, "car_id": car_id, "status": "uploaded", "analysis": analysis_result}
    except Exception as e:
        print(f"[AUTO-ANALYZE] Error analyzing car_id={car_id}: {str(e)}")
        return {"filename": file.filename, "car_id": car_id, "status": "uploaded", "analysis_error": str(e)}

# --- YOLO VIDEO ANALYSIS ---
def calculate_laplacian_variance(image):
    """Calculate Laplacian variance (sharpness score) of an image
    Higher values = sharper image
    Useful for selecting best frames for OCR"""
    if image is None or image.size == 0:
        return 0
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        return float(variance)
    except:
        return 0

@app.post("/analyze-video/{car_id}")
async def analyze_video(car_id: int, db: Session = Depends(get_db)):
    """
    Comprehensive video analysis:
    - Detect unique cars and track them across frames
    - For each car: save best frame (highest confidence)
    - Detect license plates using best.pt model
    - OCR the license plate text
    - Detect car color
    - Detect driver faces
    """
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car or not car.video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_path = car.video
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Process every second
    frame_interval = max(1, int(fps))
    frame_indices = list(range(0, frame_count, frame_interval))
    
    # Track unique vehicles by position (to avoid duplicates across frames)
    # Now tracks: vehicle detection + plate detection + OCR quality
    unique_vehicles = {}  # key: approx_position, value: best detection info
    
    detections_summary = {
        "vehicles_detected": 0,
        "plates_detected": 0,
        "faces_detected": 0,
        "frames_analyzed": len(frame_indices)
    }
    
    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue
        
        timestamp = frame_idx / fps
        frame_height, frame_width = frame.shape[:2]
        
        # Step 1: Detect vehicles using yolov8
        vehicle_results = yolo_vehicle(frame, conf=0.4)
        current_frame_vehicles = []
        
        for result in vehicle_results:
            for box in result.boxes:
                class_id = int(box.cls)
                
                # Safety check: verify class_id exists in names dict
                if class_id not in result.names:
                    print(f"Warning: class_id {class_id} not found in model names. Skipping.")
                    continue
                
                class_name = result.names[class_id]
                
                # Only process cars/trucks/buses
                if class_name not in ["car", "truck", "bus"]:
                    continue
                
                confidence = float(box.conf)
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                
                # Calculate center position for tracking
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # Create a position key (grid-based to group similar positions)
                grid_size = frame_width // 5  # Divide frame into 5 columns
                pos_key = f"{center_x // grid_size}_{center_y // (frame_height // 3)}"
                
                # OPTIMIZATION: Try to detect license plate in this frame
                # This helps us prefer frames where the plate is visible
                car_crop = frame[y1:y2, x1:x2]
                best_plate_conf = 0
                
                if car_crop.size > 0:
                    # Try to detect plate in car region
                    try:
                        plate_results = yolo_license(car_crop, conf=0.25)
                        for result in plate_results:
                            for box in result.boxes:
                                plate_conf = float(box.conf)
                                if plate_conf > best_plate_conf:
                                    best_plate_conf = plate_conf
                    except:
                        pass
                
                current_frame_vehicles.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": confidence,
                    "pos_key": pos_key,
                    "timestamp": timestamp,
                    "frame": frame.copy(),
                    "frame_idx": frame_idx,
                    "plate_confidence": best_plate_conf  # Track plate visibility
                })
        
        # For each detected vehicle, check if we have a better detection already
        # Priority: 1) Has plate detection, 2) High plate confidence, 3) High vehicle confidence
        for vehicle in current_frame_vehicles:
            pos_key = vehicle["pos_key"]
            
            # Scoring: (has_plate * 10) + (plate_confidence) + (vehicle_confidence * 0.1)
            new_score = (1 if vehicle["plate_confidence"] > 0 else 0) * 10 + \
                        vehicle["plate_confidence"] + \
                        vehicle["confidence"] * 0.1
            
            if pos_key not in unique_vehicles:
                old_score = 0
            else:
                old_score = (1 if unique_vehicles[pos_key]["plate_confidence"] > 0 else 0) * 10 + \
                            unique_vehicles[pos_key]["plate_confidence"] + \
                            unique_vehicles[pos_key]["confidence"] * 0.1
            
            # Update if new detection has better score (prioritizes plate visibility!)
            if new_score > old_score:
                unique_vehicles[pos_key] = vehicle
    
    cap.release()
    
    # Now process each unique vehicle: extract crops, detect plates, OCR, color, faces
    processed_vehicles = []
    vehicle_index = 0
    
    for pos_key, vehicle_data in unique_vehicles.items():
        frame = vehicle_data["frame"]
        x1, y1, x2, y2 = vehicle_data["bbox"]
        confidence = vehicle_data["confidence"]
        timestamp = vehicle_data["timestamp"]
        
        # Crop the car
        car_crop = frame[y1:y2, x1:x2]
        if car_crop.size == 0:
            continue
        
        # Save car crop at STANDARD SIZE (400x300) for consistent display
        STANDARD_CAR_WIDTH = 400
        STANDARD_CAR_HEIGHT = 300
        car_crop_resized = cv2.resize(car_crop, (STANDARD_CAR_WIDTH, STANDARD_CAR_HEIGHT), interpolation=cv2.INTER_AREA)
        
        crop_filename = f"car_{car_id}_v{vehicle_index}.jpg"
        cv2.imwrite(f"car_crops/{crop_filename}", car_crop_resized)
        
        # Detect car color
        car_color = detect_car_color(car_crop)
        
        # Detect license plate in this car region using best.pt
        plate_results = yolo_license(car_crop, conf=0.25)  # Lower confidence to detect more plates
        plate_image_filename = None
        plate_text = None
        plate_confidence = None
        
        best_plate_crop = None
        best_plate_conf = 0
        
        for result in plate_results:
            for box in result.boxes:
                plate_conf = float(box.conf)
                px1, py1, px2, py2 = map(int, box.xyxy[0].tolist())
                
                # Expand plate region slightly for better OCR
                pad_x = int((px2 - px1) * 0.1)
                pad_y = int((py2 - py1) * 0.1)
                px1 = max(0, px1 - pad_x)
                py1 = max(0, py1 - pad_y)
                px2 = min(car_crop.shape[1], px2 + pad_x)
                py2 = min(car_crop.shape[0], py2 + pad_y)
                
                # Crop plate from car image
                plate_crop = car_crop[py1:py2, px1:px2]
                if plate_crop.size > 0 and plate_conf > best_plate_conf:
                    best_plate_crop = plate_crop
                    best_plate_conf = plate_conf
        
        # If no plate detected in car crop, try detecting in a larger area (full frame region)
        if best_plate_crop is None:
            # Try with the full frame region around the car (with some padding)
            frame_h, frame_w = frame.shape[:2]
            pad = 50
            fx1 = max(0, x1 - pad)
            fy1 = max(0, y1 - pad)
            fx2 = min(frame_w, x2 + pad)
            fy2 = min(frame_h, y2 + pad)
            expanded_region = frame[fy1:fy2, fx1:fx2]
            
            plate_results_expanded = yolo_license(expanded_region, conf=0.2)
            for result in plate_results_expanded:
                for box in result.boxes:
                    plate_conf = float(box.conf)
                    px1, py1, px2, py2 = map(int, box.xyxy[0].tolist())
                    plate_crop = expanded_region[py1:py2, px1:px2]
                    if plate_crop.size > 0 and plate_conf > best_plate_conf:
                        best_plate_crop = plate_crop
                        best_plate_conf = plate_conf
        
        # Save plate crop and run OCR
        if best_plate_crop is not None and best_plate_crop.size > 0:
            plate_image_filename = f"plate_{car_id}_v{vehicle_index}.jpg"
            
            # Save plate at STANDARD SIZE (200x80) for consistent display
            STANDARD_PLATE_WIDTH = 200
            STANDARD_PLATE_HEIGHT = 80
            plate_crop_resized = cv2.resize(best_plate_crop, (STANDARD_PLATE_WIDTH, STANDARD_PLATE_HEIGHT), interpolation=cv2.INTER_CUBIC)
            
            # Save enhanced version of plate
            processed = preprocess_plate_image(best_plate_crop)
            if processed and 'contrast' in processed:
                # Save both original (resized) and enhanced
                cv2.imwrite(f"plate_crops/{plate_image_filename}", plate_crop_resized)
                enhanced_filename = f"plate_{car_id}_v{vehicle_index}_enhanced.jpg"
                enhanced_resized = cv2.resize(processed['contrast'], (STANDARD_PLATE_WIDTH, STANDARD_PLATE_HEIGHT), interpolation=cv2.INTER_CUBIC)
                cv2.imwrite(f"plate_crops/{enhanced_filename}", enhanced_resized)
            else:
                cv2.imwrite(f"plate_crops/{plate_image_filename}", plate_crop_resized)
            
            plate_confidence = best_plate_conf
            
            # OCR the plate with enhanced preprocessing
            plate_text = read_license_plate_text(best_plate_crop)
        
        # Detect faces/persons in the car region - DRIVER SEAT REGION
        face_image_filename = None
        face_confidence = None
        
        # Calculate driver seat region (windshield/side window view)
        car_height, car_width = car_crop.shape[:2]
        
        # Driver windshield region: RIGHT side where driver sits (Saudi Arabia/GCC)
        # In Saudi Arabia, driver sits on the RIGHT side of the car
        # Typically 55-95% of car width, 10-55% of car height (windshield area)
        driver_x1 = int(car_width * 0.55)  # Right side starts at 55%
        driver_y1 = int(car_height * 0.10)  # Top of windshield
        driver_x2 = int(car_width * 0.95)  # Right edge
        driver_y2 = int(car_height * 0.55)  # Bottom of windshield
        
        # Ensure boundaries are within car crop
        driver_x1 = max(0, driver_x1)
        driver_y1 = max(0, driver_y1)
        driver_x2 = min(car_width, driver_x2)
        driver_y2 = min(car_height, driver_y2)
        
        # Extract driver region (RIGHT side)
        driver_region = car_crop[driver_y1:driver_y2, driver_x1:driver_x2]
        
        # ALWAYS save the driver seat area as a rectangle crop, even if no face detected
        if driver_region.size > 0:
            # Save the driver seat region crop at STANDARD SIZE (200x200)
            STANDARD_DRIVER_SIZE = 200
            driver_seat_filename = f"face_{car_id}_v{vehicle_index}.jpg"
            
            # Pre-process driver region for better visibility through glass
            driver_region_enhanced = driver_region.copy()
            
            # Increase brightness and contrast for windshield glass
            lab = cv2.cvtColor(driver_region_enhanced, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            driver_region_enhanced = cv2.merge([l, a, b])
            driver_region_enhanced = cv2.cvtColor(driver_region_enhanced, cv2.COLOR_LAB2BGR)
            
            # Resize to STANDARD SIZE for consistent display
            driver_region_resized = cv2.resize(driver_region_enhanced, (STANDARD_DRIVER_SIZE, STANDARD_DRIVER_SIZE), interpolation=cv2.INTER_AREA)
            
            # Save the resized driver seat region
            cv2.imwrite(f"face_crops/{driver_seat_filename}", driver_region_resized)
            face_image_filename = driver_seat_filename
            face_confidence = 1.0  # We always capture the region
            print(f"[DRIVER] Captured driver seat region (RIGHT side) for car {car_id} vehicle {vehicle_index} - resized to {STANDARD_DRIVER_SIZE}x{STANDARD_DRIVER_SIZE}")
        
        processed_vehicles.append({
            "vehicle_index": vehicle_index,
            "crop_image": crop_filename,
            "plate_image": plate_image_filename,
            "plate_text": plate_text,
            "car_color": car_color,
            "driver_face_image": face_image_filename,
            "vehicle_confidence": confidence,
            "plate_confidence": plate_confidence,
            "face_confidence": face_confidence,
            "timestamp": timestamp
        })
        
        vehicle_index += 1
    
    # Save to database
    # Clear previous detections
    db.query(DetectedVehicle).filter(DetectedVehicle.video_id == car_id).delete()
    
    # Insert new detections
    for v in processed_vehicles:
        new_vehicle = DetectedVehicle(
            video_id=car_id,
            vehicle_index=v["vehicle_index"],
            crop_image=v["crop_image"],
            plate_image=v["plate_image"],
            plate_text=v["plate_text"],
            car_color=v["car_color"],
            driver_face_image=v["driver_face_image"],
            vehicle_confidence=v["vehicle_confidence"],
            plate_confidence=v["plate_confidence"],
            face_confidence=v["face_confidence"],
            timestamp=v["timestamp"]
        )
        db.add(new_vehicle)
    
    # Update summary
    detections_summary["vehicles_detected"] = len(processed_vehicles)
    detections_summary["plates_detected"] = sum(1 for v in processed_vehicles if v["plate_image"])
    detections_summary["faces_detected"] = sum(1 for v in processed_vehicles if v["driver_face_image"])
    
    # Update cars table
    car.analysis = json.dumps(detections_summary)
    db.commit()
    
    return {
        "status": "success",
        "summary": detections_summary,
        "vehicles": processed_vehicles
    }
