#!/bin/bash
# Start all services with docker-compose

set -e

echo "🚀 Starting ContextOS Backend..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start services
echo "📦 Building and starting services..."
docker-compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking service health..."
docker-compose ps

# Test API
echo "🔍 Testing API..."
sleep 5
curl -f http://localhost:8000/api/v1/health || echo "⚠️  API not responding yet, give it a few more seconds..."

echo ""
echo "✅ ContextOS Backend is running!"
echo ""
echo "📍 Services available at:"
echo "   - API:        http://localhost:8000"
echo "   - API Docs:   http://localhost:8000/docs"
echo "   - Flower:     http://localhost:5555"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis:      localhost:6379"
echo ""
echo "📝 View logs with: docker-compose logs -f api"
echo "🛑 Stop with: docker-compose down"

