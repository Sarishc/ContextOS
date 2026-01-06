# Quick Start Guide

## 🚀 Start the Backend (3 Steps)

### Step 1: Start Docker Desktop
Make sure Docker Desktop is running on your machine.

### Step 2: Start All Services
```bash
cd backend
./scripts/start.sh
```

### Step 3: Test the API
```bash
./scripts/test.sh
```

## 🌐 Access Points

Once running, open these URLs:

- **API Documentation**: http://localhost:8000/docs
- **API**: http://localhost:8000
- **Celery Monitor**: http://localhost:5555

## 📋 Common Commands

### Start/Stop
```bash
# Start
./scripts/start.sh

# Stop
./scripts/stop.sh

# Restart
docker-compose restart
```

### View Logs
```bash
# All services
./scripts/logs.sh

# Specific service
docker-compose logs -f api
```

### Check Status
```bash
docker-compose ps
```

### Run Tests
```bash
./scripts/test.sh
```

## 🔧 Using Makefile

```bash
# See all commands
make help

# Start services
make up

# View logs
make logs

# Test API
make test

# Stop services
make down
```

## 📊 Verify Everything Works

1. **Check Services**:
   ```bash
   docker-compose ps
   # All should show "healthy" or "running"
   ```

2. **Test Health Endpoint**:
   ```bash
   curl http://localhost:8000/api/v1/health
   # Should return: {"status":"healthy",...}
   ```

3. **Open API Docs**:
   - Go to http://localhost:8000/docs
   - Try the `/api/v1/health` endpoint
   - Create a task using `/api/v1/tasks/example`

4. **Check Flower**:
   - Go to http://localhost:5555
   - See Celery workers and tasks

## 🎯 Next Steps

1. ✅ Start the backend
2. ✅ Verify all services are running
3. ✅ Test the API endpoints
4. 📖 Read the full documentation:
   - `README.md` - Overview
   - `SETUP.md` - Detailed setup
   - `ARCHITECTURE.md` - Technical details
   - `PROJECT_SUMMARY.md` - Feature overview

5. 🛠️ Start building:
   - Add new models in `app/models/`
   - Create new endpoints in `app/api/endpoints/`
   - Add business logic in `app/services/`

## 🆘 Troubleshooting

### Docker not running
```bash
# Start Docker Desktop application
```

### Port already in use
```bash
# Stop conflicting services or change ports in docker-compose.yml
```

### Services not healthy
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

### Need to reset everything
```bash
# Stop and remove everything (WARNING: Deletes data)
docker-compose down -v

# Start fresh
./scripts/start.sh
```

## 📞 Get Help

- Review logs: `docker-compose logs`
- Check service status: `docker-compose ps`
- Read documentation in `SETUP.md`
- Review architecture in `ARCHITECTURE.md`

---

**You're all set!** 🎉

The backend is production-ready and waiting for you to add amazing features.

