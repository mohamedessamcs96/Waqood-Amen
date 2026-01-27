# Gas Station Monitoring Backend

Django REST Framework backend for the Gas Station Monitoring system.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py migrate
```

### 3. Create Admin User
```bash
python manage.py createsuperuser
```

### 4. Start Development Server
```bash
python manage.py runserver
```

### 5. Access
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/

## Structure

```
backend/
├── manage.py              Django CLI
├── requirements.txt       Python packages
│
├── GasStationProject/     Project config
│   ├── settings.py        Django settings
│   ├── urls.py            URL routing
│   ├── wsgi.py            WSGI server
│   └── asgi.py            ASGI server
│
├── apps/                  Django applications
│   ├── cars/              Car management
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── migrations/
│   │
│   └── vehicles/          Vehicle detection
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       ├── urls.py
│       ├── admin.py
│       └── migrations/
│
├── utils/                 Utilities
│   └── image_enhancement.py  CLAHE plate enhancement
│
├── car_crops/             Car crop images
├── plate_crops/           License plate images
├── face_crops/            Driver face images
├── videos/                Video files
│
├── Dockerfile             Docker build
└── docker-compose.yml     Docker compose
```

## API Endpoints

### Cars
- `GET /api/cars/` - List all cars
- `GET /api/cars/{id}/` - Get car details
- `POST /api/cars/` - Create car
- `PUT /api/cars/{id}/` - Update car
- `DELETE /api/cars/{id}/` - Delete car
- `POST /api/cars/{id}/mark_paid/` - Mark car as paid
- `POST /api/cars/{id}/mark_unpaid/` - Mark car as unpaid
- `GET /api/cars/with_analysis/` - Get cars with analysis

### Detected Vehicles
- `GET /api/detected-vehicles/` - List all vehicles
- `POST /api/detected-vehicles/` - Create vehicle record
- `GET /api/detected-vehicles/{id}/` - Get vehicle details
- `PUT /api/detected-vehicles/{id}/` - Update vehicle
- `DELETE /api/detected-vehicles/{id}/` - Delete vehicle
- `POST /api/detected-vehicles/{id}/enhance_plate/` - Enhance plate image
- `POST /api/detected-vehicles/{id}/enhance_all_images/` - Enhance all images

## Image Enhancement

Enhance low-quality license plate images using CLAHE and denoising:

```bash
# Via API
curl -X POST "http://localhost:8000/api/detected-vehicles/1/enhance_plate/?method=basic&save=true"
```

```python
# Via Python
from utils.image_enhancement import PlateImageEnhancer
import cv2

image = cv2.imread('plate.jpg')
enhanced = PlateImageEnhancer.enhance_basic(image)
cv2.imwrite('plate_enhanced.jpg', enhanced)
```

## Docker

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Logs
docker-compose logs -f gas-station-api

# Migrations
docker-compose exec gas-station-api python manage.py migrate

# Superuser
docker-compose exec gas-station-api python manage.py createsuperuser

# Stop
docker-compose down
```

## Admin Interface

Access at: http://localhost:8000/admin/

Default credentials (create with `createsuperuser`):
- Username: admin
- Password: (your choice)

## Database

Default: SQLite (db.sqlite3)

For PostgreSQL, update `GasStationProject/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gas_station',
        'USER': 'admin',
        'PASSWORD': 'admin123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Settings

Main configuration in: `GasStationProject/settings.py`

Key settings:
- `DEBUG` - Development mode
- `ALLOWED_HOSTS` - Allowed domains
- `INSTALLED_APPS` - Installed Django apps
- `DATABASES` - Database configuration
- `CORS_ALLOWED_ORIGINS` - Frontend URLs

## Production

```bash
# Collect static files
python manage.py collectstatic

# Run with Gunicorn
gunicorn GasStationProject.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Or with Docker
docker-compose up -d
```

## Notes

- All images (cars, plates, faces) are served from static directories
- CORS is enabled for frontend at localhost:3000 and localhost:5173
- Image enhancement uses OpenCV CLAHE technique
- Models support both detection and analysis
