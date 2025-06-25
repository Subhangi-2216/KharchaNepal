from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Import StaticFiles
import os
from pathlib import Path # Import Path
import logging # Add logging

# --- Define base directory for uploads ---
# This should be the same directory used in the user_settings router
UPLOAD_DIR_BASE = Path("uploads")
PROFILE_IMAGE_DIR = UPLOAD_DIR_BASE / "profile_images"

# --- Ensure upload directories exist ---
# Use the paths defined above
PROFILE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# --- Router Imports ---
from src.auth.router import router as auth_router
# Import other routers as you create them
from src.expenses.router import router as expenses_router
from src.reports.router import router as reports_router # Import reports router
# Import the new dashboard router
from src.dashboard.router import router as dashboard_router
# Import the new chatbot router
from src.chatbot.router import router as chatbot_router
# Import the new user settings router
from src.user_settings.router import router as user_settings_router
# Import the new email processing router
from src.email_processing.router import router as email_processing_router
# Import Celery app for task queuing
from celery_app import celery_app

app = FastAPI(title="Kharcha Nepal Tracker API")

# Make Celery app available to the FastAPI app
app.state.celery = celery_app

# CORS Configuration - Move this to the top before any other middleware
# Adjust origins based on your frontend URL(s)
origins = [
    "http://localhost:5173",  # Default Vite dev server port
    "http://localhost:8080",  # Port specified in your vite.config.ts
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
    "*",  # Allow all origins temporarily for testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Explicitly list all methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["*"],  # Expose all headers
    max_age=86400,  # Cache preflight requests for 24 hours
)

# --- Custom Exception Handler for Validation Errors ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log the detailed validation errors
    logging.error(f"Caught RequestValidationError: {exc.errors()}", exc_info=False) # Log specific errors
    # You can optionally log the full exception with traceback using exc_info=True
    # logging.error(f"Caught RequestValidationError", exc_info=True)

    # Return a JSON response similar to FastAPI's default
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )
# --- End Custom Exception Handler ---

# --- Mount Static Files ---
# Serve files from the 'uploads' directory at the '/uploads' URL path
# Example: A file at 'uploads/profile_images/img.jpg' will be accessible at 'http://localhost:8000/uploads/profile_images/img.jpg'
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR_BASE), name="uploads")

# Add a middleware to log all requests for debugging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log the request details
    logging.info(f"Request: {request.method} {request.url}")
    # Process the request and get the response
    response = await call_next(request)
    # Add CORS headers to all responses
    response.headers["Access-Control-Allow-Origin"] = "*"
    # Log the response status
    logging.info(f"Response status: {response.status_code}")
    return response

# Include routers
app.include_router(auth_router)
app.include_router(expenses_router)
app.include_router(reports_router) # Include reports router
app.include_router(dashboard_router) # Include the dashboard router
app.include_router(chatbot_router) # Include the chatbot router
app.include_router(user_settings_router) # Include the user settings router
app.include_router(email_processing_router) # Include the email processing router
# ... include other routers here

@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint for basic health check."""
    return {"message": "Welcome to Kharcha Nepal Tracker API"}