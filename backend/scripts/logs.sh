#!/bin/bash
# View logs from all services or a specific service

SERVICE=${1:-""}

if [ -z "$SERVICE" ]; then
    echo "📋 Viewing logs from all services..."
    docker-compose logs -f
else
    echo "📋 Viewing logs from $SERVICE..."
    docker-compose logs -f "$SERVICE"
fi

