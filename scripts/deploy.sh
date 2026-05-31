#!/bin/bash
# Deployment script for Bank Statement Distribution System

set -e

echo "=========================================="
echo "Bank Statement Distribution System Deploy"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Check if credentials exist
if [ ! -f credentials/google_drive_credentials.json ]; then
    echo "Error: Google Drive credentials not found"
    echo "Please place credentials in credentials/google_drive_credentials.json"
    exit 1
fi

# Build Docker images
echo "Building Docker images..."
docker-compose build

# Stop existing containers
echo ""
echo "Stopping existing containers..."
docker-compose down

# Start services
echo ""
echo "Starting services..."
docker-compose up -d

# Wait for database
echo ""
echo "Waiting for database to be ready..."
sleep 10

# Initialize database
echo ""
echo "Initializing database..."
docker-compose exec app python main.py init

# Check health
echo ""
echo "Checking system health..."
sleep 5
curl -f http://localhost:8080/health || echo "Health check failed"

echo ""
echo "=========================================="
echo "Deployment completed!"
echo "=========================================="
echo ""
echo "Services running:"
docker-compose ps
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
