# Kharcha Nepal - Service Management Guide

## 🚀 Quick Start

### Prerequisites
- Redis is already running (no need to start manually)
- Conda environment `kharchanepal` is activated
- Node.js version 23.11.0 is available

### Starting All Services

**Terminal 1: Backend API Server**
```bash
conda activate kharchanepal
cd KharchaNepal/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Celery Worker (for Email Sync)**
```bash
conda activate kharchanepal
cd KharchaNepal/backend
celery -A celery_app worker --loglevel=info --concurrency=2 --queues=email_processing,email_sync,ocr_processing -n worker1@%h
```

**Terminal 3: Frontend Development Server**
```bash
cd KharchaNepal/frontend
npm run dev
```

## 🔧 Service Status Checks

### Check Backend API
```bash
curl http://localhost:8000/docs
# Should return Swagger UI HTML
```

### Check Frontend
```bash
curl http://localhost:8080
# Should return React app HTML
```

### Check Redis
```bash
redis-cli ping
# Should return: PONG
```

### Check Celery Worker
```bash
conda activate kharchanepal
cd KharchaNepal/backend
celery -A celery_app inspect active
# Should show worker status
```

## 📧 Gmail OAuth & Email Sync

### Gmail Connect Button Fix
- ✅ **Fixed**: Both Gmail connect buttons now use the same styling and functionality
- ✅ **Standardized**: All buttons show "Connect Gmail Account" with Mail icon

### Email Sync Functionality
- ✅ **Fixed**: Celery tasks now use proper sync database sessions
- ✅ **Fixed**: Missing EmailAccount import added to tasks
- ✅ **Working**: Email sync will queue background tasks when Celery worker is running

### Testing Email Sync
1. Start all three services (Backend, Celery Worker, Frontend)
2. Go to http://localhost:8080/settings
3. Click "Connect Gmail Account"
4. Complete OAuth flow
5. Click the sync button (refresh icon) next to your connected account
6. Check Celery worker logs for sync activity

## 🐛 Troubleshooting

### Gmail OAuth Issues
- Ensure `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` are set in `.env`
- Check that redirect URI matches: `http://localhost:8000/api/email/oauth/callback`

### Email Sync Not Working
- Verify Celery worker is running (check Terminal 2)
- Check Redis is accessible: `redis-cli ping`
- Look for errors in Celery worker logs

### Database Issues
- Ensure PostgreSQL is running
- Check database connection in `.env` file
- Run migrations if needed: `alembic upgrade head`

## 📝 Notes

- **Redis**: Runs automatically as a service, no manual start needed
- **Celery Worker**: Must be running for email sync to work
- **OAuth Popup**: Allow popups in your browser for Gmail authorization
- **Database Sessions**: Fixed to use both async (API) and sync (Celery) sessions properly
