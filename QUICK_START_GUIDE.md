# 🚀 KharchaNepal Quick Start Guide

## 📍 Current Issue Resolution

You were in the wrong directory. Here's how to fix it:

### **Your Current Location:**
```bash
# You were here (wrong):
/Users/aasu/Desktop/OCR/kharchanepal

# You need to be here (correct):
/Users/aasu/Desktop/OCR/KharchaNepal/backend
```

## ✅ **Correct Startup Commands**

### **Option 1: Manual Commands**
```bash
# Navigate to the correct directory
cd /Users/aasu/Desktop/OCR/KharchaNepal/backend

# Activate conda environment
conda activate kharchanepal

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Option 2: Use the Startup Script**
```bash
# Navigate to project root
cd /Users/aasu/Desktop/OCR/KharchaNepal

# Run the startup script
./start_backend.sh
```

## 🔧 **Troubleshooting Common Issues**

### **Issue 1: "No config file 'alembic.ini' found"**
**Cause:** You're not in the backend directory  
**Solution:** Make sure you're in `/Users/aasu/Desktop/OCR/KharchaNepal/backend`

### **Issue 2: "Could not import module 'main'"**
**Cause:** You're not in the backend directory  
**Solution:** Navigate to the backend directory first

### **Issue 3: "conda: command not found"**
**Cause:** Conda is not in your PATH  
**Solution:** 
```bash
# Add conda to your PATH
source ~/miniconda3/etc/profile.d/conda.sh
# or
source ~/anaconda3/etc/profile.d/conda.sh
```

### **Issue 4: Environment activation fails**
**Cause:** Environment doesn't exist  
**Solution:**
```bash
# Create the environment from the yml file
cd /Users/aasu/Desktop/OCR/KharchaNepal
conda env create -f environment.yml
```

## 🌐 **Starting the Frontend**

After the backend is running, start the frontend in a new terminal:

```bash
# Navigate to frontend directory
cd /Users/aasu/Desktop/OCR/KharchaNepal/frontend

# Install dependencies (if not done already)
npm install

# Start the development server
npm run dev
```

## 📍 **Important URLs**

Once both servers are running:

- **Frontend Application:** http://localhost:8080 (or http://localhost:8081 if port conflict)
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Email Processing:** http://localhost:8080/email-processing
- **Transaction Approvals:** http://localhost:8080/transaction-approvals

## 🔍 **Verify Everything is Working**

### **1. Check Backend Health**
Visit: http://localhost:8000/docs
- You should see the FastAPI documentation page
- All email processing endpoints should be visible

### **2. Check Frontend**
Visit: http://localhost:8080
- The application should load without errors
- You should be able to navigate to different pages

### **3. Test Email Processing**
1. Go to http://localhost:8080/email-processing
2. Try connecting a Gmail account
3. Run an email sync
4. Check transaction approvals

## 🆘 **If You're Still Having Issues**

### **Check Your Current Directory:**
```bash
pwd
```

### **List Files in Current Directory:**
```bash
ls -la
```

### **Navigate to the Correct Location:**
```bash
cd /Users/aasu/Desktop/OCR/KharchaNepal/backend
```

### **Verify Backend Files Exist:**
```bash
ls -la main.py alembic.ini
```

### **Check Conda Environments:**
```bash
conda env list
```

## 📞 **Quick Commands Reference**

```bash
# Full startup sequence (copy and paste this):
cd /Users/aasu/Desktop/OCR/KharchaNepal/backend
conda activate kharchanepal
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🎯 **Success Indicators**

When everything is working correctly, you should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using WatchFiles
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

The server is now ready to accept requests!
