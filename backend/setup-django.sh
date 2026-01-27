#!/bin/bash

# Django Backend Setup Script

echo "🚀 Starting Django Setup..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating image directories..."
mkdir -p car_crops plate_crops face_crops

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Creating superuser (if needed)..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("✅ Superuser created: admin / admin")
else:
    print("✅ Superuser already exists")
END

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "✅ Django setup complete!"
echo ""
echo "To start the development server, run:"
echo "  python manage.py runserver"
echo ""
echo "Admin panel: http://localhost:8000/admin/"
echo "API docs: http://localhost:8000/api/"
echo ""
