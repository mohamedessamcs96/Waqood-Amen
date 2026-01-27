#!/bin/bash

# Gas Station Monitoring Website - Docker Rebuild Script
# Usage: chmod +x rebuild.sh && ./rebuild.sh

echo "🚀 Gas Station Monitoring Website - Docker Rebuild"
echo "=================================================="
echo ""

PROJECT_DIR="/Users/herotech/Desktop/Gas Station Monitoring Website"
cd "$PROJECT_DIR" || exit 1

echo "📍 Working directory: $PROJECT_DIR"
echo ""

# Step 1: Stop old container
echo "⏹️  Stopping old container..."
docker stop gas-station-api 2>/dev/null || echo "   (No running container)"

# Step 2: Remove old container
echo "🗑️  Removing old container..."
docker rm gas-station-api 2>/dev/null || echo "   (No container to remove)"

# Step 3: Build new image
echo ""
echo "🔨 Building Docker image..."
docker build -t gas-station-api:latest . || {
    echo "❌ Build failed!"
    exit 1
}

# Step 4: Run new container
echo ""
echo "🚀 Starting new container..."
docker run -d \
  --name gas-station-api \
  -p 8000:8000 \
  -v "$(pwd)/videos:/app/videos" \
  -v "$(pwd)/cars.db:/app/cars.db" \
  gas-station-api:latest || {
    echo "❌ Container failed to start!"
    exit 1
}

# Step 5: Wait for container to start
echo ""
echo "⏳ Waiting for API to start..."
sleep 3

# Step 6: Verify
echo ""
echo "✅ Checking API health..."
if curl -s http://localhost:8000/cars > /dev/null; then
    echo "✅ API is running successfully!"
    echo ""
    echo "📊 Container Status:"
    docker ps | grep gas-station-api
    echo ""
    echo "📝 Recent Logs:"
    docker logs gas-station-api | tail -5
else
    echo "⚠️  API not responding yet. Check logs:"
    docker logs gas-station-api
fi

echo ""
echo "=================================================="
echo "🎉 Setup Complete!"
echo ""
echo "🌐 API URL: http://localhost:8000"
echo "🖥️  Frontend: http://localhost:3000"
echo ""
echo "Next steps:"
echo "1. Go to http://localhost:3000"
echo "2. Upload a video with license plates"
echo "3. Click Analyze"
echo "4. Check All Cars tab for results"
echo ""
echo "View logs: docker logs gas-station-api -f"
echo "=================================================="
