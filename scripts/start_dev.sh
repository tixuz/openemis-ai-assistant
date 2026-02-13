#!/bin/bash

# Development startup script - starts all services

set -e

echo "🚀 Starting AI Automation System (Development Mode)"
echo "=================================================="

# Check if .env file exists in docker directory
if [ ! -f docker/.env ]; then
    echo "⚠️  Warning: docker/.env not found"
    echo "Creating from docker/.env.example..."
    cp docker/.env.example docker/.env
    echo "✅ Created docker/.env - please edit with your settings"
    echo ""
fi

# Check if LLM server is running
echo "🔍 Checking LLM server..."
if curl -s -f -o /dev/null "http://localhost:8080/v1/models" 2>/dev/null; then
    echo "✅ LLM server is running on port 8080"
else
    echo "⚠️  LLM server not detected on port 8080"
    echo "   Start it with: ./start_ai.sh"
    echo ""
fi

# Start Docker containers
echo ""
echo "🐳 Starting Docker containers..."
cd docker
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check service health
echo ""
echo "🏥 Checking service health..."

if curl -s -f -o /dev/null "http://localhost:8000/health" 2>/dev/null; then
    echo "✅ FastAPI backend: http://localhost:8000"
else
    echo "❌ FastAPI backend not responding"
fi

if curl -s -f -o /dev/null "http://localhost:3000/" 2>/dev/null; then
    echo "✅ Flask frontend: http://localhost:3000"
else
    echo "❌ Flask frontend not responding"
fi

echo ""
echo "=================================================="
echo "✨ System is ready!"
echo ""
echo "📍 Access points:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "🔐 Default credentials:"
echo "   - Username: admin"
echo "   - Password: admin123"
echo ""
echo "📊 View logs:"
echo "   docker-compose -f docker/docker-compose.yml logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose -f docker/docker-compose.yml down"
echo "=================================================="
