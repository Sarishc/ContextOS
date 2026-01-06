#!/bin/bash
# Stop all services

set -e

echo "🛑 Stopping ContextOS Backend..."

docker-compose down

echo "✅ Services stopped successfully!"
echo ""
echo "💡 To remove volumes as well, run: docker-compose down -v"

