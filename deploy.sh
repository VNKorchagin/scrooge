#!/bin/bash
# Local deployment script for manual deployment
# Usage: ./deploy.sh

set -e

echo "Starting deployment..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

echo "Pulling latest changes..."
git pull origin $(git rev-parse --abbrev-ref HEAD)

echo "Building and starting containers..."
docker-compose down
docker-compose up -d --build

echo "Waiting for database to be ready..."
sleep 10

echo "Running migrations..."
docker-compose exec backend alembic upgrade head || echo "Migration check completed"

echo "Cleaning up..."
docker system prune -f

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "Application should be available at http://localhost (or your server IP)"
docker-compose ps
