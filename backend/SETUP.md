# Setup Guide

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (v20.10+)
- **Docker Compose** (v2.0+)
- **Git**
- **Python 3.11+** (optional, for local development)

## Quick Start with Docker

### 1. Start Docker Desktop

Make sure Docker Desktop is running on your machine.

### 2. Clone and Navigate

```bash
cd backend
```

### 3. Configure Environment

The project includes a default `.env` file. For production, create your own:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Start All Services

Using the provided script:

```bash
./scripts/start.sh
```

Or using docker-compose directly:

```bash
docker-compose up -d
```

Or using the Makefile:

```bash
make up
```

### 5. Verify Services

Check that all services are running:

```bash
docker-compose ps
```

All services should show "healthy" or "running" status.

### 6. Test the API

Run the test script:

```bash
./scripts/test.sh
```

Or manually:

```bash
curl http://localhost:8000/api/v1/health
```

## Service URLs

Once running, access:

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Flower (Celery Monitor)**: http://localhost:5555
- **PostgreSQL**: localhost:5432
  - User: `contextos`
  - Password: `contextos_password`
  - Database: `contextos_db`
- **Redis**: localhost:6379

## Useful Commands

### Using Scripts

```bash
# Start all services
./scripts/start.sh

# Stop all services
./scripts/stop.sh

# View logs
./scripts/logs.sh

# View specific service logs
./scripts/logs.sh api

# Test API
./scripts/test.sh
```

### Using Makefile

```bash
# See all available commands
make help

# Start services
make up

# Stop services
make down

# View logs
make logs

# Test API
make test

# Restart services
make restart

# Open shell in API container
make shell-api

# Open PostgreSQL shell
make shell-db

# Open Redis CLI
make shell-redis
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api

# Rebuild and start
docker-compose up -d --build

# Stop and remove volumes
docker-compose down -v
```

## Database Migrations

### Create a New Migration

```bash
# Auto-generate migration from model changes
docker-compose exec api alembic revision --autogenerate -m "description"

# Create empty migration
docker-compose exec api alembic revision -m "description"
```

### Apply Migrations

```bash
# Apply all pending migrations
docker-compose exec api alembic upgrade head

# Apply specific migration
docker-compose exec api alembic upgrade <revision>

# Rollback one migration
docker-compose exec api alembic downgrade -1

# Rollback to specific migration
docker-compose exec api alembic downgrade <revision>
```

### View Migration History

```bash
# Show current version
docker-compose exec api alembic current

# Show migration history
docker-compose exec api alembic history
```

## Local Development (Without Docker)

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL and Redis

Use Docker for just the databases:

```bash
docker-compose up -d db redis
```

### 4. Update Environment Variables

Edit `.env` and change:
```env
POSTGRES_HOST=localhost
REDIS_HOST=localhost
```

### 5. Run the Application

```bash
# Start API
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Run Celery Worker (in another terminal)

```bash
celery -A app.services.celery_app worker --loglevel=info
```

### 7. Run Flower (optional, in another terminal)

```bash
celery -A app.services.celery_app flower
```

## Troubleshooting

### Docker Issues

**Problem**: Docker daemon not running
```bash
# Solution: Start Docker Desktop application
```

**Problem**: Port already in use
```bash
# Solution: Check what's using the port
lsof -i :8000  # Check port 8000
# Stop the process or change port in docker-compose.yml
```

**Problem**: Permission denied on scripts
```bash
# Solution: Make scripts executable
chmod +x scripts/*.sh
```

### Database Issues

**Problem**: Database connection failed
```bash
# Solution: Check if PostgreSQL container is running
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

**Problem**: Migration conflicts
```bash
# Solution: Reset database (WARNING: This deletes all data)
docker-compose down -v
docker-compose up -d
```

### Redis Issues

**Problem**: Redis connection failed
```bash
# Solution: Check if Redis container is running
docker-compose ps redis

# View Redis logs
docker-compose logs redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### API Issues

**Problem**: API not responding
```bash
# Solution: Check API logs
docker-compose logs api

# Restart API
docker-compose restart api

# Rebuild API container
docker-compose up -d --build api
```

**Problem**: Import errors in Python
```bash
# Solution: Rebuild the container
docker-compose build api
docker-compose up -d api
```

## Development Workflow

### 1. Making Code Changes

When you edit code in the `app/` directory:

- Changes are automatically reflected (volume mounted)
- API auto-reloads when files change (in development mode)
- No need to rebuild container for Python changes

### 2. Adding New Dependencies

When you add to `requirements.txt`:

```bash
# Rebuild the container
docker-compose build api
docker-compose up -d api
```

### 3. Adding New Models

1. Create model in `app/models/`
2. Import in `alembic/env.py`
3. Generate migration:
   ```bash
   docker-compose exec api alembic revision --autogenerate -m "add new model"
   ```
4. Apply migration:
   ```bash
   docker-compose exec api alembic upgrade head
   ```

### 4. Adding New Endpoints

1. Create endpoint file in `app/api/endpoints/`
2. Add router to `app/api/router.py`
3. Test at http://localhost:8000/docs

### 5. Running Tests

```bash
# Run all tests
docker-compose exec api pytest

# Run with coverage
docker-compose exec api pytest --cov=app

# Run specific test file
docker-compose exec api pytest tests/test_health.py
```

## Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=False`
- [ ] Use strong database credentials
- [ ] Set Redis password
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Use environment-specific .env files
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerts

### Environment Variables

Create a production `.env` file:

```env
APP_ENV=production
DEBUG=False
LOG_LEVEL=WARNING
SECRET_KEY=your-very-strong-secret-key-here
POSTGRES_PASSWORD=strong-database-password
REDIS_PASSWORD=strong-redis-password
CORS_ORIGINS=["https://yourdomain.com"]
```

### Deployment Options

1. **Docker Compose** (Simple)
   - Copy files to server
   - Run `docker-compose up -d`

2. **Kubernetes** (Scalable)
   - Use provided Dockerfile
   - Create K8s manifests
   - Deploy to cluster

3. **Cloud Platforms**
   - AWS ECS/Fargate
   - Google Cloud Run
   - Azure Container Instances

## Support

For issues and questions:
- Check the troubleshooting section
- Review Docker logs: `docker-compose logs`
- Verify configuration in `.env`
- Ensure all services are healthy: `docker-compose ps`

## Next Steps

- [ ] Review the API documentation at http://localhost:8000/docs
- [ ] Explore the example endpoints
- [ ] Add your own models and endpoints
- [ ] Integrate AI services (see README.md)
- [ ] Set up CI/CD pipeline
- [ ] Configure monitoring and logging

