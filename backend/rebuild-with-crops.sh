#!/bin/bash

# Gas Station Monitoring - Individual Car Crops Rebuild
# This script rebuilds the Docker container with the latest changes

set -e

PROJECT_DIR="/Users/herotech/Desktop/Gas Station Monitoring Website"
cd "$PROJECT_DIR"

echo "🚀 Rebuilding Docker container with Individual Car Crops..."
echo "============================================================"

# Stop old container
echo "⏹️  Stopping old container..."
docker stop gas-station-api 2>/dev/null || true

# Remove old container
echo "🗑️  Removing old container..."
docker rm gas-station-api 2>/dev/null || true

# Build new image
echo "🔨 Building Docker image..."
docker build -t gas-station-api:latest . || {
    echo "❌ Build failed!"
    exit 1
}

# Run new container with car_crops volume
echo "🚀 Starting new container..."
docker run -d \
  --name gas-station-api \
  -p 8000:8000 \
  -v "$(pwd)/videos:/app/videos" \
  -v "$(pwd)/car_crops:/app/car_crops" \
  -v "$(pwd)/cars.db:/app/cars.db" \
  gas-station-api:latest || {
    echo "❌ Container failed to start!"
    exit 1
}

# Wait for startup
sleep 3

# Test API
echo ""
echo "✅ Testing API..."
if curl -s http://localhost:8000/cars > /dev/null 2>&1; then
    echo "✅ API is running!"
else
    echo "⚠️  API not responding. Check logs:"
    docker logs gas-station-api | tail -20
    exit 1
fi

echo ""
echo "============================================================"
echo "🎉 Rebuild complete!"
echo ""
echo "📝 Changes:"
echo "  ✓ Per-second frame extraction"
echo "  ✓ Individual car crop images"
echo "  ✓ New detected_vehicles table"
echo "  ✓ Updated frontend UI"
echo ""
echo "📝 Next steps:"
echo "  1. Hard refresh frontend: Cmd+Shift+R"
echo "  2. Go to All Cars tab"
echo "  3. Upload video with cars"
echo "  4. Click Analyze"
echo "  5. View individual cropped cars"
echo ""
echo "🔗 URLs:"
echo "  API:      http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "📊 View logs:"
echo "  docker logs gas-station-api -f"
echo "============================================================"
