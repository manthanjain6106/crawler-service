#!/bin/bash

# Deployment script for the crawler service
# Supports development and production environments

set -e

ENVIRONMENT=${1:-development}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo "Deploying to PRODUCTION environment"
else
    echo "Deploying to DEVELOPMENT environment"
fi

echo "Using compose file: $COMPOSE_FILE"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "Error: docker-compose is not installed"
    exit 1
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs data ssl

# Set proper permissions
chmod 755 logs data

# Pull latest images (for production)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Pulling latest images..."
    docker-compose -f $COMPOSE_FILE pull
fi

# Build and start services
echo "Building and starting services..."
docker-compose -f $COMPOSE_FILE up --build -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Check service health
echo "Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Crawler service is healthy"
else
    echo "❌ Crawler service is not responding"
    echo "Checking logs..."
    docker-compose -f $COMPOSE_FILE logs crawler-service
    exit 1
fi

# Check Redis health
if docker-compose -f $COMPOSE_FILE exec redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis is not responding"
    exit 1
fi

# Show running services
echo "Running services:"
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "🚀 Deployment completed successfully!"
echo ""
echo "Service URLs:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo ""
echo "To view logs:"
echo "  docker-compose -f $COMPOSE_FILE logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose -f $COMPOSE_FILE down"
echo ""
echo "To scale workers (production only):"
echo "  docker-compose -f $COMPOSE_FILE up --scale crawler-worker=5 -d"
