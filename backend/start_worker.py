#!/usr/bin/env python3
"""
Script to start Celery worker for Kharcha Nepal email processing.
"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery_app import celery_app

if __name__ == "__main__":
    # Start the Celery worker
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=2",
        "--queues=email_processing,email_sync,ocr_processing",
    ])
