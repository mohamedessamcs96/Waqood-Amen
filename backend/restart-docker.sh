#!/bin/bash

echo "🔧 Stopping existing containers..."
docker compose down 2>/dev/null || echo "No containers running"

echo ""
echo "🐳 Building and starting Docker container..."
docker compose up -d --build

echo ""
echo "⏳ Waiting for container to start (30 seconds)..."
sleep 30

echo ""
echo "📋 Checking container status..."
docker compose ps

echo ""
echo "📊 Checking logs for errors..."
docker compose logs gas-station-api | tail -50

echo ""
echo "✅ Testing backend connection..."
curl -s http://localhost:8000/cars | python3 -m json.tool || echo "Backend not responding yet, waiting..."

sleep 5

echo ""
echo "🚀 Attempting second test..."
curl -s http://localhost:8000/cars | python3 -m json.tool
