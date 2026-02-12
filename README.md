# وقود آمن — Waqood Secure

## Smart Gas Station Monitoring & Protection System

An AI-powered gas station monitoring system that uses **YOLOv8** computer vision and **PaddleOCR** (with EasyOCR fallback) to automatically detect vehicles, read KSA license plates (Arabic & English), identify car colors, and capture driver regions from uploaded surveillance videos. The system tracks payment status and alerts staff when a vehicle with **unpaid history** returns.

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [How to Run](#how-to-run)
5. [How to Upload a Video](#how-to-upload-a-video)
6. [How the Analyzer Works](#how-the-analyzer-works)
7. [Admin Panel Guide](#admin-panel-guide)
8. [API Endpoints Reference](#api-endpoints-reference)
9. [Default Credentials](#default-credentials)
10. [Troubleshooting](#troubleshooting)

---

## Features

| Feature | Description |
|---|---|
| 🎥 **Video Upload** | Upload surveillance video (MP4, AVI, MOV, MKV, WebM — up to 500MB) |
| 🚗 **Vehicle Detection** | YOLOv8 detects cars, trucks, and buses per frame |
| 🔢 **License Plate OCR** | YOLOv8 plate model + **PaddleOCR** (primary) + EasyOCR (fallback) for KSA Arabic plates |
| 🖼️ **Image Preprocessing** | CLAHE, denoising, Otsu thresholding, morphological cleanup for better OCR accuracy |
| 🎨 **Car Color Detection** | HSV-based dominant color identification (White, Black, Silver, Red, Blue, etc.) |
| 👤 **Driver Region Capture** | Extracts and enhances the driver-side region of each vehicle |
| 💰 **Payment Tracking** | Mark vehicles as Paid / Unpaid from the dashboard |
| 🚨 **Unpaid Alert** | Red banner + highlighted rows when a returning plate has unpaid history |
| 🔄 **Auto-Refresh** | All Cars page refreshes every 15 seconds automatically |
| 🌐 **Bilingual UI** | Arabic (RTL) and English (LTR) toggle |
| 🔐 **Authentication** | Login, Register, role-based access (Admin / Employee) |
| 📊 **Dashboard** | Statistics charts, recent activity, vehicle breakdown |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons |
| **Backend** | Django 4.2.8, Django REST Framework 3.14.0, Gunicorn |
| **Database** | PostgreSQL 15 (Docker) |
| **AI / CV** | YOLOv8 (Ultralytics), PaddleOCR (primary), EasyOCR (fallback), OpenCV |
| **Containers** | Docker, Docker Compose |

---

## Project Structure

```
Gas Station Monitoring Website/
├── backend/                      # Django backend (Docker)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── entrypoint.sh             # Migrations, superuser, Gunicorn start
│   ├── manage.py
│   ├── requirements.txt
│   ├── yolov8n.pt                # YOLO vehicle detection model
│   ├── best.pt                   # YOLO license plate detection model
│   ├── GasStationProject/        # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── authentication/       # Login, Register, Logout, Me
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   └── urls.py
│   │   ├── cars/                 # Car CRUD, Upload, Analysis, Payment
│   │   │   ├── views.py          # Core logic + YOLO analysis
│   │   │   ├── models.py         # Car model (plate, paid, video, analysis)
│   │   │   ├── serializers.py
│   │   │   ├── urls.py
│   │   │   └── management/commands/analyze_video.py  # Background analysis
│   │   └── vehicles/             # Detected vehicles from analysis
│   │       ├── models.py         # DetectedVehicle model
│   │       ├── views.py
│   │       └── serializers.py
│   ├── videos/                   # Uploaded video files (Docker volume)
│   ├── car_crops/                # Detected vehicle image crops
│   ├── plate_crops/              # Detected license plate crops
│   └── face_crops/               # Driver region crops
│
├── web/                          # React frontend
│   ├── src/
│   │   ├── App.tsx               # Main app: routing, auth, navigation
│   │   ├── api.ts                # All API calls to backend
│   │   └── components/
│   │       ├── Login.tsx          # Login & Register page
│   │       ├── AdminDashboard.tsx # Admin stats + charts
│   │       ├── EmployeeDashboard.tsx  # Employee view
│   │       ├── AllCars.tsx        # All detected vehicles (auto-refresh)
│   │       ├── UnpaidCars.tsx     # Unpaid vehicles only
│   │       ├── CarTable.tsx       # Vehicle table with images + actions
│   │       ├── PaymentModal.tsx   # Payment confirmation modal
│   │       └── PlateEditModal.tsx # Edit plate text modal
│   ├── package.json
│   └── vite.config.ts
│
├── upload.py                     # CLI upload script with analysis polling
└── cars.MP4                      # Sample video file
```

---

## How to Run

### Prerequisites

- **Docker Desktop** installed and running
- **Node.js** 18+ and **npm** (for the frontend)

### Step 1: Start the Backend (Docker)

```bash
cd backend
docker compose up -d --build
```

This starts two containers:

| Container | Port | Description |
|---|---|---|
| `gas-station` | `8000` | Django API + Gunicorn (2 workers, 120s timeout) |
| `gas-station-db` | `5432` | PostgreSQL 15 database |

The entrypoint automatically:
1. Waits for PostgreSQL to be ready
2. Runs database migrations
3. Creates the default **admin** superuser
4. Collects static files
5. Starts Gunicorn on port 8000

**Verify the backend is running:**

```bash
curl http://localhost:8000/api/cars/
```

You should get a JSON response (empty list `[]` or paginated result).

### Step 2: Start the Frontend

```bash
cd web
npm install
npm run dev
```

The frontend runs at **http://localhost:5173** (Vite dev server).

### Step 3: Open the App

Open your browser and go to:

```
http://localhost:5173
```

You'll see the login page. Use the default credentials (see [Default Credentials](#default-credentials)).

---

## How to Upload a Video

There are **two ways** to upload a video for analysis:

### Option 1: Using the CLI Script (Recommended)

From the project root directory:

```bash
# Upload with auto-generated plate ID
python upload.py --video cars.MP4

# Upload with a specific plate number
python upload.py --video cars.MP4 --plate "س ع ب 5873"

# Upload a different video
python upload.py --video /path/to/surveillance.mp4 --plate "ABC-123"
```

The script will:
1. ✅ Upload the video file to the backend
2. 🚨 Show an alert if the plate has unpaid history
3. 🔍 Poll the analysis status every 5 seconds (up to 10 minutes)
4. ✅ Print the number of vehicles detected when complete

### Option 2: Using cURL

```bash
curl -X POST http://localhost:8000/api/cars/upload_video/ \
  -F "video=@cars.MP4" \
  -F "plate=ABC-123"
```

### What Happens After Upload

1. The video is **instantly saved** and a `Car` record is created
2. A **background subprocess** starts: `python manage.py analyze_video <car_id>`
3. YOLO analysis runs in the background (does NOT block the API)
4. Results appear in the dashboard once analysis completes

You can check analysis status:

```bash
curl http://localhost:8000/api/cars/analysis_status/?car_id=1
```

Response:
```json
{
  "car_id": 1,
  "analyzed": true,
  "vehicle_count": 3,
  "analysis": "{\"vehicles_detected\": 3, \"plates_detected\": 2, \"faces_detected\": 3}"
}
```

---

## How the Analyzer Works

The analysis pipeline processes each uploaded video through multiple AI models:

### Pipeline Overview

```
Video Upload → Save File → Create Car Record → Background Subprocess
                                                       ↓
                                            ┌─────────────────────┐
                                            │  analyze_video.py   │
                                            │  Management Command  │
                                            └─────────────────────┘
                                                       ↓
                                            ┌─────────────────────┐
                                            │  1. YOLOv8 Vehicle  │
                                            │     Detection       │
                                            │  (yolov8n.pt)       │
                                            │  Classes: car,      │
                                            │  truck, bus         │
                                            └─────────────────────┘
                                                       ↓
                                            ┌─────────────────────┐
                                            │  2. YOLOv8 Plate    │
                                            │     Detection       │
                                            │  (best.pt)          │
                                            └─────────────────────┘
                                                       ↓
                                            ┌─────────────────────┐
                                            │  3. OCR Plate Read  │
                                            │  PaddleOCR (primary)│
                                            │  EasyOCR (fallback) │
                                            │  + KSA Format Clean │
                                            └─────────────────────┘
                                                       ↓
                                            ┌─────────────────────┐
                                            │  4. Color Detection │
                                            │  HSV Analysis       │
                                            └─────────────────────┘
                                                       ↓
                                            ┌─────────────────────┐
                                            │  5. Driver Region   │
                                            │  Crop + Enhance     │
                                            └─────────────────────┘
                                                       ↓
                                            ┌─────────────────────┐
                                            │  6. Save Results    │
                                            │  DetectedVehicle DB │
                                            │  + Image Crops      │
                                            └─────────────────────┘
```

### Detailed Steps

#### 1. Frame Sampling
- Opens the video with OpenCV
- Samples **1 frame per second** (based on FPS)
- This reduces processing time while maintaining accuracy

#### 2. Vehicle Detection (YOLOv8)
- Uses `yolov8n.pt` model (general object detection)
- Filters for classes: **car**, **truck**, **bus** (confidence ≥ 0.4)
- Tracks unique vehicles using a **grid-based position key** (`cx//grid _ cy//grid`)
- Keeps the best frame per vehicle (prioritizes frames where a plate is visible)

#### 3. License Plate Detection (YOLOv8)
- Uses `best.pt` model (custom-trained plate detection)
- Runs on each vehicle crop (confidence ≥ 0.25)
- Adds **10% padding** around detected plate for better OCR

#### 4. Plate OCR (PaddleOCR + EasyOCR Dual Strategy)

We use **PaddleOCR** as the primary OCR engine because it has significantly better Arabic text recognition accuracy (~93-95%) compared to EasyOCR (~75-80%). EasyOCR serves as a fallback.

**Why PaddleOCR over EasyOCR for KSA plates?**

| Feature | EasyOCR | PaddleOCR |
|---|---|---|
| **Arabic Accuracy** | ~75-80% | ~93-95% |
| **Speed per plate** | ~2 seconds | ~0.5 seconds |
| **KSA plate handling** | Generic | Better Arabic character separation |
| **License** | Apache 2.0 | Apache 2.0 |

**Dual-OCR Strategy:** Each plate image is processed 4 ways, and the highest-confidence result wins:

1. **PaddleOCR on color image** — best for clear plates
2. **PaddleOCR on binary image** — best for low-contrast plates
3. **EasyOCR on color image** — fallback
4. **EasyOCR on binary image** — last resort

**Preprocessing pipeline** (applied before OCR):

| Step | Method | Purpose |
|---|---|---|
| Resize | Scale to 400px width | Consistent input size |
| Grayscale | `cv2.cvtColor` | Remove color noise |
| CLAHE | `clipLimit=3.0, tileGrid=(8,8)` | Enhance contrast |
| Denoising | `fastNlMeansDenoising(h=12)` | Remove noise |
| Otsu Threshold | `THRESH_BINARY + THRESH_OTSU` | Binarize text (better than adaptive for plates) |
| Morphological Close | `kernel=(2,2)` | Fill small gaps in characters |

**KSA Plate Format Cleanup:**

Saudi plates follow the format: **3 Arabic letters + 4 digits** (e.g. `أ ب ج 1234`)

After OCR, the text is cleaned:
- Remove all special characters (`$ | _ ?` etc.)
- Extract Arabic letters (keep up to 3)
- Extract digits (Arabic-Indic ٠-٩ are converted to Western 0-9)
- Format output: `أ ب ج 1234`

#### 5. Car Color Detection
- Extracts the **center region** (30-70% height, 20-80% width) of the car crop
- Converts to HSV color space
- Classifies based on Hue, Saturation, and Value thresholds:
  - White, Black, Silver/Gray, Red, Orange, Yellow, Green, Blue, Purple

#### 6. Driver Region Capture
- Crops the **right side** of the vehicle (55-95% width, 10-55% height)
  - Right side is standard for Saudi Arabia (driver seat)
- Applies CLAHE enhancement for better visibility
- Saves as 200×200 image

#### 7. Save Results
- Creates `DetectedVehicle` records in the database
- Saves image crops to Docker volumes:
  - `car_crops/car_{id}_v{idx}.jpg` (400×300)
  - `plate_crops/plate_{id}_v{idx}.jpg` (200×80)
  - `face_crops/face_{id}_v{idx}.jpg` (200×200)
- Updates the `Car.analysis` JSON field with summary

---

## Admin Panel Guide

### Login Page

- Enter username and password
- Choose role: **Admin** or **Employee**
- New users can register with the **Register** tab
- Supports Arabic/English language toggle

### Admin Dashboard (`/admin`)

The admin dashboard shows:
- **Total Vehicles** — count of all detected cars
- **Unpaid Vehicles** — count of vehicles with `paid = false`
- **Today's Activity** — vehicles processed today
- **Charts** — Recharts bar/line charts for vehicle statistics
- **Recent Activity** — latest detected vehicles with thumbnails

### Employee Dashboard (`/employee`)

A simplified view for gas station employees showing:
- Recent vehicle detections
- Quick payment status overview

### All Cars Page (`/all-cars`)

The main vehicle management page:
- **Auto-refreshes** every 15 seconds
- **Manual refresh** button (↻ icon)
- **Unpaid Alert Banner** — red warning at the top when unpaid vehicles exist
- Vehicle table showing for each detected vehicle:

| Column | Description |
|---|---|
| **Vehicle Image** | Cropped image of the detected car |
| **Plate Image** | Cropped license plate image |
| **Plate Text** | OCR-read plate number (editable) |
| **Car Color** | Detected color (White, Black, Red, etc.) |
| **Driver** | Driver region image |
| **Confidence** | YOLO detection confidence % |
| **Status** | Paid ✅ / Unpaid ❌ badge |
| **Actions** | Mark Paid / Mark Unpaid buttons |

- **Red highlighted rows**: Unpaid vehicles have a red left border + light red background
- **Edit Plate**: Click on any plate text to manually correct it
- **Pagination**: Navigate through pages of results

### Unpaid Cars Page (`/unpaid`)

- Shows only vehicles with `paid = false`
- Same table layout as All Cars
- Quick access to mark vehicles as paid

### Navigation

| Route | Access | Description |
|---|---|---|
| `/admin` | Admin only | Admin dashboard with statistics |
| `/employee` | Employee only | Employee simplified dashboard |
| `/all-cars` | Both | Full vehicle list with management |
| `/unpaid` | Both | Unpaid vehicles only |

---

## API Endpoints Reference

### Authentication

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/auth/login/` | Login with username & password | No |
| POST | `/api/auth/register/` | Register new user | No |
| POST | `/api/auth/logout/` | Logout and delete token | Yes |
| GET | `/api/auth/me/` | Get current user info | Yes |

**Login Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Login Response:**
```json
{
  "success": true,
  "token": "abc123...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "is_admin": true
  }
}
```

### Cars (Upload, Analysis, Payment)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| GET | `/api/cars/` | List all cars (paginated) | No |
| POST | `/api/cars/upload_video/` | Upload video + start analysis | No |
| POST | `/api/cars/{id}/analyze/` | Manually trigger analysis | No |
| GET | `/api/cars/with_analysis/` | Cars with vehicle count | No |
| GET | `/api/cars/check_plate/?plate=X` | Check if plate has unpaid visits | No |
| GET | `/api/cars/analysis_status/?car_id=X` | Poll analysis completion | No |
| POST | `/api/cars/{id}/mark_paid/` | Mark car as paid | No |
| POST | `/api/cars/{id}/mark_unpaid/` | Mark car as unpaid | No |

**Upload Video Request:**
```bash
curl -X POST http://localhost:8000/api/cars/upload_video/ \
  -F "video=@video.mp4" \
  -F "plate=ABC-123"
```

**Upload Video Response:**
```json
{
  "success": true,
  "car_id": 5,
  "message": "Video uploaded. Analysis started in background.",
  "video_name": "video.mp4",
  "plate": "ABC-123",
  "alert": {
    "type": "unpaid_return",
    "message": "⚠️ This plate (ABC-123) has a previous UNPAID visit!",
    "previous_car_id": 2
  }
}
```

### Detected Vehicles

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/detected-vehicles/` | List all detected vehicles (paginated) |
| PUT | `/api/detected-vehicles/{id}/update_plate/` | Update plate text for a vehicle |

**Image URLs:**
- Vehicle crop: `http://localhost:8000/car_crops/{filename}`
- Plate crop: `http://localhost:8000/plate_crops/{filename}`
- Driver crop: `http://localhost:8000/face_crops/{filename}`

---

## Default Credentials

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin (superuser) |

The admin superuser is automatically created when the Docker container starts for the first time.

To register additional users, use the Register tab on the login page or the API:

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "employee1", "password": "pass123", "password_confirm": "pass123", "role": "employee"}'
```

---

## Troubleshooting

### Port 8000 already in use

Another application may be running on port 8000. Kill it first:

```bash
lsof -ti:8000 | xargs kill -9
```

Then restart Docker:

```bash
cd backend
docker compose down
docker compose up -d --build
```

### Backend returns 404 on login

Make sure Docker is running and no other process is on port 8000:

```bash
docker ps   # Should show gas-station and gas-station-db
curl http://localhost:8000/api/auth/login/   # Should return 405 (Method Not Allowed, not 404)
```

### Analysis seems stuck / no images appearing

Check the analysis log inside the container:

```bash
docker exec -it gas-station tail -f /app/analysis.log
```

Analysis can take **5-15 minutes** depending on video length and CPU. The All Cars page auto-refreshes every 15 seconds — images will appear once analysis completes.

### Check analysis status manually

```bash
curl http://localhost:8000/api/cars/analysis_status/?car_id=1
```

If `"analyzed": false`, analysis is still running.

### Docker container keeps restarting

Check logs:

```bash
docker logs gas-station --tail 100
```

Common causes:
- Database not ready yet (wait a few seconds)
- Out of memory (the container needs at least 2GB RAM)

### Frontend can't connect to backend

Make sure:
1. Backend is on `http://localhost:8000`
2. Frontend is on `http://localhost:5173`
3. CORS is configured (already set in `docker-compose.yml` for ports 3000 and 5173)

### Rebuild everything from scratch

```bash
cd backend
docker compose down -v         # Remove containers + volumes (deletes DB data!)
docker compose up -d --build   # Rebuild and start fresh
```

---

## Docker Commands Quick Reference

```bash
# Start containers
cd backend && docker compose up -d --build

# Stop containers
docker compose down

# View logs
docker logs gas-station -f
docker logs gas-station-db -f

# Enter container shell
docker exec -it gas-station bash

# Check analysis log
docker exec -it gas-station tail -f /app/analysis.log

# Run analysis manually inside container
docker exec -it gas-station python manage.py analyze_video --all

# Check database
docker exec -it gas-station-db psql -U admin -d gas_station -c "SELECT * FROM cars;"
docker exec -it gas-station-db psql -U admin -d gas_station -c "SELECT * FROM detected_vehicles;"

# Full rebuild (clears data)
docker compose down -v && docker compose up -d --build
```

---

## License

This project is for internal gas station monitoring use.

---

**وقود آمن — Waqood Secure** | Smart Monitoring & Protection System
