#!/bin/bash
set -e

echo "=== Waiting for database... ==="
# Wait for PostgreSQL to be ready
while ! python -c "
import os, sys
try:
    import psycopg2
    conn = psycopg2.connect(os.environ.get('DATABASE_URL', ''))
    conn.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "Database not ready, waiting 2 seconds..."
    sleep 2
done

echo "=== Database is ready! ==="

echo "=== Running migrations... ==="
python manage.py migrate --noinput

echo "=== Creating superuser if not exists... ==="
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser admin created.')
else:
    print('Superuser admin already exists.')
"

echo "=== Collecting static files... ==="
python manage.py collectstatic --noinput || true

echo "=== Starting Gunicorn... ==="
exec gunicorn GasStationProject.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 120
