# Kharcha Nepal - Automated Expense Tracking

A comprehensive expense tracking application with OCR capabilities and automated email-based expense extraction from banks and e-wallets.

## 🚀 Features

### Core Features
- **OCR Expense Scanning**: Upload receipts and extract expense data automatically
- **Manual Expense Entry**: Add expenses manually with categories and descriptions
- **Expense Reports**: Generate detailed reports with charts and analytics
- **User Authentication**: Secure login and user management
- **Profile Management**: Update user profiles with avatar support

### 🆕 **NEW: Automated Email Expense Tracking**
- **Gmail Integration**: Connect Gmail accounts via OAuth2
- **Automatic Email Parsing**: Extract transaction data from bank/e-wallet emails
- **Transaction Approval Queue**: Review and approve extracted transactions
- **Privacy-First**: All data encrypted and processed securely
- **Background Processing**: Celery-based async email processing

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based authentication
- **Background Tasks**: Celery with Redis broker
- **Email Processing**: Gmail API integration with OAuth2
- **Security**: Encrypted credential storage, CORS protection

### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development
- **UI Components**: Shadcn/ui with Tailwind CSS
- **State Management**: React Context for authentication
- **Routing**: React Router for navigation

### Infrastructure
- **Message Broker**: Redis for Celery tasks
- **File Storage**: Local file system for uploads
- **Email Processing**: Background workers for async processing

## 📋 Prerequisites

Before running the application, ensure you have:

### System Requirements
- **Python 3.10+** (with conda/miniconda)
- **Node.js 18+** and npm
- **PostgreSQL 12+**
- **Redis 6+**

### Environment Setup
1. **Conda Environment**: `kharchanepal`
2. **Database**: PostgreSQL database named `expense_tracker`
3. **Gmail API**: Google Cloud Console project with Gmail API enabled

## 🛠️ Installation & Setup

### 1. Clone Repository
\`\`\`bash
git clone <repository-url>
cd KharchaNepal
\`\`\`

### 2. Backend Setup
\`\`\`bash
cd backend

# Create and activate conda environment
conda create -n kharchanepal python=3.10
conda activate kharchanepal

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration (see Environment Variables section)

# Run database migrations
alembic upgrade head

# Install additional dependencies for email processing
pip install celery==5.3.4 redis==5.0.1 google-api-python-client==2.134.0 google-auth==2.30.0 google-auth-httplib2==0.2.0 google-auth-oauthlib==1.2.0 emails==0.6.0 aiosqlite
\`\`\`

### 3. Frontend Setup
\`\`\`bash
cd frontend

# Install dependencies
npm install

# Install additional UI dependencies
npm install dlv autoprefixer postcss
\`\`\`

### 4. Database Setup
\`\`\`bash
# Create PostgreSQL database
createdb expense_tracker

# Or using psql
psql -c "CREATE DATABASE expense_tracker;"
\`\`\`

### 5. Redis Setup
\`\`\`bash
# Install Redis (macOS)
brew install redis

# Start Redis
redis-server --daemonize yes

# Verify Redis is running
redis-cli ping
\`\`\`

## 🔧 Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

\`\`\`env
# Database Configuration
DATABASE_URL="postgresql+asyncpg://username:password@localhost:5432/expense_tracker"

# JWT Configuration
JWT_SECRET_KEY="your-secret-key-here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Celery Configuration (Redis)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Gmail API Configuration (from Google Cloud Console)
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/email/oauth/callback

# Encryption Key (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-encryption-key-here
\`\`\`

## 🚀 Running the Application

### Method 1: Start All Services Individually

#### 1. Start Redis (if not running)
\`\`\`bash
redis-server --daemonize yes
\`\`\`

#### 2. Start Backend (FastAPI)
\`\`\`bash
cd backend
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate kharchanepal
uvicorn main:app --reload --port 8000 --host 0.0.0.0
\`\`\`

#### 3. Start Celery Worker (Background Tasks)
\`\`\`bash
# In a new terminal
cd backend
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate kharchanepal
celery -A celery_app worker --loglevel=info
\`\`\`

#### 4. Start Frontend (React)
\`\`\`bash
# In a new terminal
cd frontend
npm run dev
\`\`\`

### Method 2: Using the Start Script (Recommended)
\`\`\`bash
# Make the script executable
chmod +x start_all_servers.sh

# Run all services
./start_all_servers.sh
\`\`\`

## 🌐 Access URLs

Once all services are running:

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Redis**: localhost:6379

## 📱 Using the Application

### 1. User Registration/Login
1. Go to http://localhost:8080
2. Register a new account or login with existing credentials
3. Complete your profile setup

### 2. Traditional Expense Tracking
- **Add Expenses**: Use the "+" button to add manual expenses
- **OCR Scanning**: Upload receipt images for automatic data extraction
- **View Reports**: Access detailed analytics and charts

### 3. 🆕 **Automated Email Expense Tracking**

#### Connect Gmail Account
1. Go to **Settings** → **Email Processing** tab
2. Click **"Connect Gmail Account"**
3. Complete Google OAuth consent
4. Your Gmail account will be connected and listed

#### Review Transaction Approvals
1. Go to **Settings** → **Transaction Approvals** tab
2. Review extracted transaction data
3. Approve or reject transactions
4. Approved transactions become expenses automatically

#### Sync Emails
- Emails are synced automatically in the background
- Manual sync available via "Sync Now" button
- Only financial emails from banks/e-wallets are processed

## 🧪 Testing

### Run Backend Tests
\`\`\`bash
cd backend
conda activate kharchanepal

# Run all tests
python run_automated_tests.py

# Run specific test categories
pytest tests/unit/email_processing/ -v
pytest tests/integration/ -v
\`\`\`

### Test Email Processing
\`\`\`bash
# Test encryption
pytest tests/unit/email_processing/test_encryption.py -v

# Test email parsing
pytest tests/unit/email_processing/test_email_parser.py -v

# Test API endpoints
pytest tests/integration/test_email_processing_api.py -v
\`\`\`

## 🔒 Security Features

### Email Processing Security
- **OAuth2 Authentication**: Secure Gmail access without storing passwords
- **Encrypted Credentials**: All OAuth tokens encrypted at rest
- **Minimal Permissions**: Read-only Gmail access
- **Privacy-First**: No email content stored permanently
- **Secure Processing**: Background workers with encrypted communication

### General Security
- **JWT Authentication**: Secure API access
- **Password Hashing**: Bcrypt password encryption
- **CORS Protection**: Configured for frontend domain
- **Input Validation**: Comprehensive request validation

## 🐛 Troubleshooting

### Common Issues

#### Backend Won't Start
\`\`\`bash
# Check conda environment
conda activate kharchanepal
python --version

# Check database connection
python -c "from database import get_db; print('Database connection OK')"

# Check dependencies
pip install -r requirements.txt
\`\`\`

#### Frontend Build Errors
\`\`\`bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run build
\`\`\`

#### Redis Connection Issues
\`\`\`bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server --daemonize yes

# Check Redis logs
redis-cli monitor
\`\`\`

#### Gmail OAuth Issues
1. **Check Google Cloud Console**:
   - Gmail API is enabled
   - OAuth consent screen configured
   - Correct redirect URI: `http://localhost:8000/api/email/oauth/callback`

2. **Check Environment Variables**:
   - `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` are correct
   - `GMAIL_REDIRECT_URI` matches Google Cloud Console

3. **Check Backend Logs**:
   - Look for OAuth-related errors in FastAPI logs

### Email Processing Issues
\`\`\`bash
# Check Celery worker status
celery -A celery_app inspect active

# Check Redis connection
redis-cli ping

# Test email processing components
python -c "from src.email_processing.gmail_service import gmail_service; print('Gmail service OK')"
\`\`\`

## 📊 Monitoring

### Check Service Status
\`\`\`bash
# Backend health
curl http://localhost:8000/

# Frontend health
curl http://localhost:8080/

# Redis health
redis-cli ping

# Celery worker status
celery -A celery_app inspect active
\`\`\`

### View Logs
\`\`\`bash
# Backend logs (in uvicorn terminal)
# Celery logs (in celery terminal)
# Frontend logs (in npm terminal)

# Redis logs
redis-cli monitor
\`\`\`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review the logs for error messages
3. Ensure all prerequisites are installed
4. Verify environment variables are set correctly

For additional support, please create an issue in the repository.