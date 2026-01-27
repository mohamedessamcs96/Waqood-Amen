FROM python:3.10-slim

WORKDIR /app

# System dependencies (optimized for CPU, PaddleOCR, and Django)
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 libxrender-dev libgomp1 git curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --upgrade pip

# Copy ONLY requirements.txt first (this creates a cached layer)
COPY requirements.txt .

# Install dependencies with cache mount (this layer is cached)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Copy application code LAST (changes frequently, won't invalidate cache)
COPY . .

# CPU optimization environment variables
ENV OMP_NUM_THREADS=4
ENV OPENBLAS_NUM_THREADS=4
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=GasStationProject.settings
ENV PYTHONDONTWRITEBYTECODE=1

# Collect static files
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Run Django with Gunicorn for production-ready setup
CMD ["gunicorn", "GasStationProject.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "sync", "--timeout", "120"]