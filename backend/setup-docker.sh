#!/bin/bash

# Gas Station Monitoring Website - Docker Setup Guide
# Run this script to start the backend

echo "🐳 Gas Station Monitoring Website - Docker Startup"
echo "=================================================="
echo ""

# Step 1: Navigate to the project directory
echo "📁 Navigating to project directory..."
cd "/Users/herotech/Desktop/Gas Station Monitoring Website" || exit 1

echo ""
echo "🛑 Step 1: Stopping existing containers..."
docker compose down 2>/dev/null || echo "   ℹ️  No containers running"

echo ""
echo "🔨 Step 2: Building Docker image (this may take 2-3 minutes)..."
docker compose build

echo ""
echo "🚀 Step 3: Starting container..."
docker compose up -d

echo ""
echo "⏳ Step 4: Waiting for container to fully start..."
sleep 20

echo ""
echo "📊 Step 5: Checking container status..."
docker compose ps

echo ""
echo "📋 Step 6: Checking logs..."
docker compose logs gas-station-api | tail -30

echo ""
echo "🧪 Step 7: Testing backend connection..."
sleep 5

# Try to connect
if curl -s http://localhost:8000/cars > /dev/null 2>&1; then
    echo "✅ Backend is RUNNING! Testing endpoint..."
    curl -s http://localhost:8000/cars | python3 -m json.tool | head -20
else
    echo "⚠️  Backend not responding yet. Check logs with:"
    echo "   docker compose logs -f gas-station-api"
fi

echo ""
echo "=================================================="
echo "✨ Docker setup complete!"
echo ""
echo "📝 Useful commands:"
echo "   View logs:     docker compose logs -f gas-station-api"
echo "   Stop:          docker compose down"
echo "   Restart:       docker compose restart"
echo "   Remove all:    docker compose down -v"
echo ""
