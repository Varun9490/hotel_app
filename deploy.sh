#!/bin/bash

# Hotel Project Deployment Script for Linux

set -e  # Exit on any error

echo "Starting Hotel Project deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null
then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null
then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Pull latest code (if using git)
if [ -d ".git" ]; then
    echo "Pulling latest code from repository..."
    git pull
fi

# Build and start services
echo "Building and starting Docker containers..."
docker-compose -f docker-compose.simple.yml up -d --build

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker exec hotel_web python manage.py migrate

# Collect static files
echo "Collecting static files..."
docker exec hotel_web python manage.py collectstatic --noinput

echo "Deployment completed successfully!"
echo "Access the application at http://localhost:8000"
echo "To create a superuser, run: docker exec -it hotel_web python manage.py createsuperuser"