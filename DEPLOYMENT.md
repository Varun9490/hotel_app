# Production Deployment Guide

This guide provides instructions for deploying the Hotel Management System to a production environment.

## Prerequisites

1. Python 3.8+
2. MySQL or PostgreSQL database
3. Redis server
4. Web server (Nginx recommended)
5. Process manager (Supervisor or systemd)

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd hotel_project
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit the `.env` file with your actual configuration values.

### 5. Database Setup

Create the database and run migrations:

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 8. Start Services

#### Start Redis
```bash
redis-server
```

#### Start Celery Worker (if using async tasks)
```bash
celery -A config worker -l info
```

#### Start the Application Server

Using Gunicorn:
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### 9. Configure Web Server (Nginx Example)

Create an Nginx configuration file:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }

    location /media/ {
        alias /path/to/your/project/media/;
    }
}
```

### 10. Setup Process Manager (Supervisor Example)

Create a supervisor configuration file `/etc/supervisor/conf.d/hotel_project.conf`:

```ini
[program:hotel_project]
command=/path/to/your/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000
directory=/path/to/your/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/hotel_project.log

[program:hotel_project_celery]
command=/path/to/your/venv/bin/celery -A config worker -l info
directory=/path/to/your/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/hotel_project_celery.log
```

## Security Considerations

1. Always set `DEBUG=False` in production
2. Use strong secret keys
3. Configure allowed hosts properly
4. Use HTTPS in production
5. Set proper file permissions
6. Regularly update dependencies
7. Implement proper backup strategies

## User Group Management

The system uses three main user groups:
- **Admins**: Full access to all features
- **Staff**: Access to guest management, voucher operations, and operational features
- **Users**: Limited access (currently not used in the UI)

To create these groups, use the Django admin interface or run the init_roles management command:

```bash
python manage.py init_roles
```

## Monitoring and Maintenance

1. Monitor application logs regularly
2. Set up health checks
3. Implement automated backups
4. Monitor resource usage
5. Keep dependencies updated

## Troubleshooting

### Common Issues

1. **Database Connection Errors**: Check database credentials and ensure the database server is running
2. **Permission Denied**: Check file permissions and user privileges
3. **Static Files Not Loading**: Ensure `collectstatic` was run and web server configuration is correct
4. **Celery Not Working**: Check Redis connection and Celery worker status

### Useful Commands

```bash
# Check application status
python manage.py check --deploy

# View logs
tail -f /var/log/hotel_project.log

# Restart services
sudo supervisorctl restart hotel_project
sudo supervisorctl restart hotel_project_celery
```