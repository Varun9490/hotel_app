# Hotel Project - Docker Deployment Guide

This guide explains how to containerize and deploy the Hotel Project using Docker and Docker Compose.

## Prerequisites

Before you begin, ensure you have the following installed:
- Docker Engine 20.10+
- Docker Compose 1.29+

## Project Structure

The project includes the following Docker-related files:
- `Dockerfile`: Defines the application container
- `docker-compose.yml`: Full deployment with MySQL, Redis, Celery workers
- `docker-compose.simple.yml`: Simplified deployment with just MySQL
- `.dockerignore`: Specifies files to exclude from Docker builds

## Dockerizing the Application

### 1. Building the Docker Image

To build the Docker image locally:

```bash
docker build -t hotel-app .
```

### 2. Running with Docker Compose (Recommended)

#### Full Deployment (with Celery and Redis)

```bash
docker-compose up -d
```

This will start:
- MySQL database
- Redis server
- Web application
- Celery worker
- Celery beat scheduler

#### Simple Deployment (Web + MySQL only)

```bash
docker-compose -f docker-compose.simple.yml up -d
```

### 3. Initial Setup

After starting the containers, you need to run migrations and create a superuser:

```bash
# Run migrations
docker exec -it hotel_web python manage.py migrate

# Create superuser
docker exec -it hotel_web python manage.py createsuperuser

# Collect static files
docker exec -it hotel_web python manage.py collectstatic --noinput

# Load initial data (optional)
docker exec -it hotel_web python manage.py loaddata initial_data.json
```

## Deploying to Linux Server

### 1. Install Docker on Ubuntu/Debian

```bash
# Update package index
sudo apt-get update

# Install Docker
sudo apt-get install docker.io docker-compose -y

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group (optional)
sudo usermod -aG docker $USER
```

### 2. Deploy the Application

```bash
# Clone or copy your project to the server
git clone <your-repo-url>
cd hotel_project

# Start the application
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 3. Production Considerations

1. **Environment Variables**: Create a `.env` file with secure passwords:
   ```
   DJANGO_SECRET_KEY=your-very-long-secret-key
   DJANGO_DEBUG=False
   DB_PASSWORD=your-secure-db-password
   ```

2. **HTTPS**: Use a reverse proxy like Nginx with Let's Encrypt SSL certificates.

3. **Backup**: Regularly backup your database volume:
   ```bash
   docker run --rm -v hotel_project_db_data:/data -v $(pwd):/backup ubuntu tar czf /backup/db_backup.tar.gz -C /data .
   ```

## Useful Docker Commands

### Managing Containers

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f web

# Stop containers
docker-compose down

# Restart specific service
docker-compose restart web

# Execute commands in container
docker exec -it hotel_web bash
```

### Database Management

```bash
# Access MySQL shell
docker exec -it hotel_db mysql -u hotel_user -p temp

# Backup database
docker exec hotel_db mysqldump -u hotel_user -p temp > backup.sql

# Restore database
docker exec -i hotel_db mysql -u hotel_user -p temp < backup.sql
```

## Scaling the Application

To scale the web application:

```bash
docker-compose up -d --scale web=3
```

## Troubleshooting

### Common Issues

1. **Permission denied errors**: Ensure Docker is running and your user has permissions.
2. **Port conflicts**: Change exposed ports in docker-compose.yml if needed.
3. **Database connection errors**: Check DB credentials and ensure the database container is running.

### Checking Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs web
docker-compose logs db
```

## Updating the Application

To deploy updates:

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```