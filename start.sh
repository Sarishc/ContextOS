#!/bin/bash

# Start script for ContextOS

echo "🚀 Starting ContextOS..."
echo ""

# Check if backend is running
if ! docker ps | grep -q contextos-api; then
    echo "📦 Starting backend services..."
    cd backend
    docker-compose up -d
    cd ..
    echo "⏳ Waiting for backend to be ready..."
    sleep 5
else
    echo "✅ Backend already running"
fi

# Check backend health
echo "🔍 Checking backend health..."
BACKEND_URL="http://localhost:8000"
if curl -s "${BACKEND_URL}/health" > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend health check failed. Please check backend logs."
    echo "   Run: cd backend && docker-compose logs -f"
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    echo "VITE_API_URL=http://localhost:8000" > .env
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend
echo ""
echo "🌐 Starting frontend..."
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

npm run dev

