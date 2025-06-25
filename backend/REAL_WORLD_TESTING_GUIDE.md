# 🚀 Real-World Testing Guide for Automated Expense Tracking

## ✅ **AUTOMATED TESTING COMPLETE!**

All automated tests are now **PASSING** ✅:
- **Dependencies**: pytest ✅, celery ✅, redis ✅, alembic ✅
- **Database Models**: All email processing models ✅
- **Encryption**: Credential encryption/decryption ✅
- **Email Parsing**: Financial email detection and pattern extraction ✅
- **Gmail Service**: OAuth2 and API integration ✅
- **Celery Tasks**: Background task processing ✅
- **Database Migration**: Schema updates ✅
- **Integration Tests**: Complete workflow testing ✅

**Total: 8/8 PASSED** 🎯

---

## 🌍 Real-World Testing Instructions

Now that all automated tests pass, here's how to test the system with actual Gmail accounts and real emails:

### 📋 **Prerequisites Checklist**

Before starting real-world testing, ensure:
- [ ] Redis server is running (`redis-cli ping` returns `PONG`)
- [ ] Database migration applied (`alembic upgrade head`)
- [ ] All dependencies installed in conda environment `kharchanepal`
- [ ] Google Cloud Console project set up with Gmail API enabled

---

## 🔧 **Step 1: Environment Setup**

### 1.1 Create Production Environment File
```bash
cd KharchaNepal/backend
cp .env.example .env
```

### 1.2 Configure Required Settings
Edit `.env` with your actual values:

```env
# Database (use your existing database)
DATABASE_URL=postgresql://username:password@localhost:5432/kharcha_nepal

# JWT (use your existing settings)
JWT_SECRET_KEY=your-existing-jwt-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Celery (Redis must be running)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Gmail API (from Google Cloud Console)
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/email/oauth/callback

# Encryption key (generate new one)
ENCRYPTION_KEY=your-base64-encryption-key
```

### 1.3 Generate Encryption Key
```bash
conda activate kharchanepal
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```
Copy the output to your `.env` file.

---

## 🔑 **Step 2: Google Cloud Console Setup**

### 2.1 Create/Configure Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing one
3. Enable Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 2.2 Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Set authorized redirect URI: `http://localhost:8000/api/email/oauth/callback`
5. Copy Client ID and Client Secret to `.env`

### 2.3 Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill required fields:
   - App name: "Kharcha Nepal Expense Tracker"
   - User support email: your email
   - Developer contact: your email
4. Add scopes: `https://www.googleapis.com/auth/gmail.readonly`
5. Add test users (your Gmail accounts for testing)

---

## 🚀 **Step 3: Start All Services**

### 3.1 Terminal 1: Start FastAPI Application
```bash
conda activate kharchanepal
cd KharchaNepal/backend
uvicorn main:app --reload --port 8000
```

### 3.2 Terminal 2: Start Celery Worker
```bash
conda activate kharchanepal
cd KharchaNepal/backend
python start_worker.py
```

### 3.3 Terminal 3: Monitor Redis (Optional)
```bash
redis-cli monitor
```

### 3.4 Verify Services
```bash
# Check FastAPI
curl http://localhost:8000/
# Should return: {"message":"Welcome to Kharcha Nepal Tracker API"}

# Check Celery worker logs
# Should see: "ready." in worker terminal

# Check Redis
redis-cli ping
# Should return: PONG
```

---

## 👤 **Step 4: Create Test User Account**

### 4.1 Register New User
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-test-email@example.com",
    "password": "testpassword123",
    "name": "Test User"
  }'
```

### 4.2 Login and Get JWT Token
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your-test-email@example.com&password=testpassword123"
```

**Save the `access_token` from response:**
```bash
export JWT_TOKEN="your-jwt-token-here"
```

---

## 📧 **Step 5: Connect Gmail Account**

### 5.1 Initiate OAuth Flow
```bash
curl -X GET "http://localhost:8000/api/email/oauth/authorize" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### 5.2 Complete OAuth in Browser
1. Copy the `authorization_url` from response
2. Open URL in browser
3. Sign in with Gmail account that has financial emails
4. Grant permissions to read Gmail
5. You'll be redirected to callback URL
6. Check URL parameters for success/error

### 5.3 Verify Account Connection
```bash
curl -X GET "http://localhost:8000/api/email/accounts" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

Should return your connected Gmail account.

---

## 📬 **Step 6: Test Email Synchronization**

### 6.1 Sync Emails from Gmail
```bash
# Replace {account_id} with actual account ID from previous step
curl -X POST "http://localhost:8000/api/email/accounts/1/sync" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### 6.2 Monitor Processing
Watch the Celery worker terminal for task execution logs:
- Email sync tasks
- Email processing tasks
- OCR extraction tasks

### 6.3 Check Sync Results
The response should show:
```json
{
  "message": "Email sync completed",
  "account_id": 1,
  "status": "completed",
  "synced_messages": 5,
  "messages": [...]
}
```

---

## 🗄️ **Step 7: Verify Database Records**

### 7.1 Check Email Accounts
```sql
SELECT id, email_address, is_active, last_sync_at, created_at 
FROM email_accounts;
```

### 7.2 Check Synced Messages
```sql
SELECT id, subject, sender, received_at, processing_status, has_attachments 
FROM email_messages 
ORDER BY received_at DESC 
LIMIT 10;
```

### 7.3 Check Transaction Approvals
```sql
SELECT 
    id, 
    user_id, 
    email_message_id, 
    approval_status, 
    confidence_score,
    extracted_data->>'source' as source,
    created_at
FROM transaction_approvals 
ORDER BY created_at DESC 
LIMIT 10;
```

### 7.4 Check Generated Expenses
```sql
SELECT 
    id, 
    amount, 
    description, 
    category,
    is_ocr_entry,
    email_message_id,
    extraction_confidence,
    created_at
FROM expenses 
WHERE email_message_id IS NOT NULL
ORDER BY created_at DESC 
LIMIT 10;
```

---

## 🧪 **Step 8: Test Different Email Types**

### 8.1 Test Financial Emails
Send test emails to your Gmail account or use existing ones:

**Bank Transaction Emails:**
- Subject: "Transaction Alert"
- From: bank@yourbank.com
- Content: Payment of $50.00 to Amazon

**Payment Processor Emails:**
- Subject: "Payment Receipt"
- From: service@paypal.com
- Content: You sent $25.00 to John Doe

**E-wallet Emails:**
- Subject: "Payment Successful"
- From: noreply@esewa.com.np
- Content: Rs. 1,500 paid to Grocery Store

### 8.2 Test Email with Attachments
Send emails with receipt images attached to test OCR processing.

### 8.3 Re-sync and Verify
After sending test emails:
```bash
curl -X POST "http://localhost:8000/api/email/accounts/1/sync" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## 📊 **Step 9: Performance Testing**

### 9.1 Test Large Email Volume
1. Connect Gmail account with many financial emails
2. Sync and monitor processing time
3. Check Celery worker performance
4. Verify database performance

### 9.2 Test Concurrent Users
1. Create multiple user accounts
2. Connect different Gmail accounts
3. Sync simultaneously
4. Monitor system resources

---

## 🔍 **Step 10: Validation Checklist**

### ✅ **Core Functionality**
- [ ] Gmail OAuth flow completes successfully
- [ ] Email accounts are stored and encrypted
- [ ] Financial emails are detected correctly
- [ ] Transaction patterns are extracted accurately
- [ ] OCR processes image attachments
- [ ] Transaction approvals are created
- [ ] Database records are consistent

### ✅ **Security**
- [ ] OAuth credentials are encrypted in database
- [ ] JWT authentication works correctly
- [ ] API endpoints require proper authorization
- [ ] No sensitive data in logs

### ✅ **Performance**
- [ ] Email sync completes within reasonable time
- [ ] Celery tasks process without errors
- [ ] Database queries are efficient
- [ ] Memory usage is stable

### ✅ **Error Handling**
- [ ] Invalid OAuth codes are handled gracefully
- [ ] Network errors don't crash the system
- [ ] Malformed emails are processed safely
- [ ] Database errors are logged properly

---

## 🎯 **Success Criteria**

Your automated expense tracking is working correctly if:

1. **OAuth Flow**: ✅ Gmail accounts connect successfully
2. **Email Sync**: ✅ Financial emails are fetched and stored
3. **Pattern Extraction**: ✅ Transaction data is extracted from emails
4. **OCR Processing**: ✅ Receipt images are processed
5. **Approval Queue**: ✅ Transaction approvals are created for review
6. **Database Integrity**: ✅ All data is stored correctly
7. **Background Processing**: ✅ Celery tasks execute without errors
8. **Security**: ✅ Credentials are encrypted and secure

## 🎉 **Congratulations!**

If all steps pass, your automated expense tracking feature is **production-ready** and successfully:
- Connects to Gmail accounts securely
- Automatically detects financial emails
- Extracts transaction data using OCR and pattern matching
- Creates approval queues for user review
- Processes everything in the background
- Maintains security and data integrity

Your Kharcha Nepal OCR project now has powerful automated expense tracking capabilities! 🚀
